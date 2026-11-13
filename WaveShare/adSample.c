/*
 * adSample - record from the Waveshare High-Precision AD HAT (ADS1263).
 *
 *   adSample [options] <channels> <rate> <seconds>
 *
 *   channels  1 or 2
 *   rate      1200, 2400, 4800, 7200, 14400, 19200  (1 channel)
 *             1200                                  (2 channels)
 *   seconds   0.1 .. 60
 *
 * Options:
 *   -o FILE   output file (default adSample_YYYYmmdd_HHMMSS.ads)
 *   -i P[,P]  analog inputs for channel 1[,2] (AIN0..AIN9, default 0,1);
 *             each is measured against AINCOM
 *   -r REF    reference: avdd (default, +-5 V full scale, same as the
 *             Waveshare demo) or int (internal 2.5 V, +-2.5 V, lower noise)
 *   -f N      sinc filter order 1..4 (1 channel only; default 1 = widest
 *             bandwidth; higher orders give better alias rejection)
 *
 * 1 channel: the ADC free-runs on its own clock at the native data rate
 *   and every conversion is read.  The kernel timestamps and counts every
 *   DRDY edge, so a conversion missed by user space is detected exactly,
 *   repaired by linear interpolation and reported.
 * 2 channels: the ADS1263 has one ADC behind a multiplexer and needs about
 *   230 us to settle after every channel switch, so 2 channels max out at
 *   ~2100 pairs/s.  Sampling is paced by the Pi clock: at each tick channel
 *   1 is converted, then channel 2 (about 0.23 ms later), in one-shot mode.
 *
 * Output: a 64-byte header followed by interleaved little-endian int32
 * samples; volts = sample / 2^31 * vref.  See bin2wav.py.
 *
 * Exit status: 0 ok, 1 error (no file written), 3 file written but
 * samples were repaired or mistimed (details printed).
 */
#define _GNU_SOURCE
#include "ads1263.h"

#include <getopt.h>
#include <math.h>
#include <sched.h>
#include <signal.h>
#include <stdlib.h>
#include <sys/mman.h>

#define SPI_HZ 8000000
#define RT_CPU 3

typedef struct __attribute__((packed)) {
    char magic[4];          /* "ADS1" */
    uint16_t version;       /* 1 */
    uint16_t header_bytes;  /* 64 */
    uint16_t channels;
    uint16_t sample_format; /* 1 = int32 little-endian */
    uint32_t sample_rate;   /* nominal, Hz */
    uint64_t frames;
    double measured_rate;   /* ADC rate measured against the Pi clock (0 = n/a) */
    double vref;            /* volts = sample / 2^31 * vref */
    int64_t start_unix_ns;
    uint32_t repaired;      /* samples lost and filled by interpolation */
    uint32_t timing_errors; /* 2 ch: samples taken > 20 us late */
    uint8_t inputs[2];      /* AIN number per channel (vs AINCOM) */
    uint8_t ref;            /* 0 = internal 2.5 V, 1 = AVDD */
    uint8_t filter;         /* sinc order */
    uint32_t reserved;
} file_header_t;

_Static_assert(sizeof(file_header_t) == 64, "header must be 64 bytes");

static const struct { unsigned rate; uint8_t code; } rates[] = {
    { 1200, ADS_DR_1200 },  { 2400, ADS_DR_2400 },   { 4800, ADS_DR_4800 },
    { 7200, ADS_DR_7200 },  { 14400, ADS_DR_14400 }, { 19200, ADS_DR_19200 },
};
#define MAX_RATE_2CH 1200

static volatile sig_atomic_t stop_requested;
static void on_signal(int sig) { (void)sig; stop_requested = 1; }

static void usage(void)
{
    fprintf(stderr,
            "usage: adSample [-o FILE] [-i P[,P]] [-r avdd|int] [-f 1-4] <channels> <rate> <seconds>\n"
            "  channels: 1 or 2\n"
            "  rate:     1200 2400 4800 7200 14400 19200 (1 channel); 1200 (2 channels)\n"
            "  seconds:  0.1 to 60\n");
}

static int parse_long(const char *s, long *out)
{
    char *end;
    errno = 0;
    long v = strtol(s, &end, 10);
    if (errno || end == s || *end)
        return -1;
    *out = v;
    return 0;
}

static void realtime_setup(void)
{
    cpu_set_t cs;
    CPU_ZERO(&cs);
    CPU_SET(RT_CPU, &cs);
    sched_setaffinity(0, sizeof cs, &cs);
    struct sched_param sp = { .sched_priority = 50 };
    if (sched_setscheduler(0, SCHED_FIFO, &sp) < 0)
        fprintf(stderr, "note: running without real-time priority; for best reliability run\n"
                        "      'sudo setcap cap_sys_nice,cap_ipc_lock+ep adSample' once\n");
}

static void wait_until(double t)
{
    while (ads_now() < t)
        ;
}

/* Wait for DRDY low; returns 0, or -1 on timeout / stop request. */
static int wait_drdy(ads_t *a, double timeout)
{
    double t_end = ads_now() + timeout;
    for (;;) {
        int l = ads_drdy(a);
        if (l == 0)
            return 0;
        if (l < 0 || ads_now() > t_end)
            return -1;
    }
}

/* Fill samples whose ok[] flag is 0 by linear interpolation (stride = channels). */
static uint32_t repair(int32_t *x, uint8_t *ok, size_t n, int stride)
{
    uint32_t bad = 0;
    ssize_t prev = -1;
    for (size_t i = 0; i <= n; i++) {
        if (i < n && !ok[i * stride])
            continue;
        size_t gap0 = prev + 1;
        if (i > gap0) {
            bad += i - gap0;
            for (size_t j = gap0; j < i; j++) {
                int32_t *y = &x[j * stride];
                if (prev < 0 && i == n)
                    *y = 0;
                else if (prev < 0)
                    *y = x[i * stride];
                else if (i == n)
                    *y = x[prev * stride];
                else {
                    double f = (double)(j - prev) / (double)(i - prev);
                    *y = (int32_t)lrint(x[prev * stride] + f * ((double)x[i * stride] - x[prev * stride]));
                }
            }
        }
        prev = i;
    }
    return bad;
}

/* ---- 1 channel: ADC-paced continuous conversion ----------------------- */

static int acquire_1ch(ads_t *a, uint8_t dr_code, unsigned rate, int filter, uint8_t mux,
                       int32_t *x, size_t n, size_t *got, uint32_t *repaired, double *measured,
                       uint32_t *mismatch)
{
    const size_t SKIP = 1;   /* discard the first conversion after START */
    const size_t EXTRA = 16; /* read a few spare conversions past the end */
    const size_t B = 256;    /* events per block for the latency envelope */
    size_t cap = n + SKIP + EXTRA;
    size_t ecap = cap + 4096;
    int32_t *rv = malloc(cap * sizeof *rv);
    double *rt = malloc(cap * sizeof *rt);
    uint8_t *rok = malloc(cap);
    double *et = malloc(ecap * sizeof *et);
    double *ek = malloc(ecap * sizeof *ek);
    double *env = NULL;
    uint8_t *ok = calloc(n, 1);
    int rc = -1;
    if (!rv || !rt || !rok || !et || !ek || !ok) {
        fprintf(stderr, "error: out of memory\n");
        goto out;
    }
    memset(rv, 0, cap * sizeof *rv); /* pre-fault pages before timing starts */
    memset(rt, 0, cap * sizeof *rt);
    memset(rok, 0, cap);
    memset(et, 0, ecap * sizeof *et);
    memset(ek, 0, ecap * sizeof *ek);
    /* Lock the (now allocated and touched) buffers in RAM; best effort.
     * MCL_FUTURE is avoided: without CAP_IPC_LOCK it makes later
     * allocations fail once RLIMIT_MEMLOCK is reached. */
    mlockall(MCL_CURRENT);

    if (ads_wreg_verify(a, ADS_REG_MODE0, 0x00) ||                  /* continuous */
        ads_wreg_verify(a, ADS_REG_MODE1, (uint8_t)((filter - 1) << 5)) ||
        ads_wreg_verify(a, ADS_REG_MODE2, 0x80 | dr_code) ||       /* PGA bypass */
        ads_wreg_verify(a, ADS_REG_INPMUX, mux))
        goto out;

    /* Discard stale edges; the first edge after START is conversion 0. */
    struct gpio_v2_line_event ev[256];
    while (ads_events(a, ev, 256) > 0)
        ;
    if (ads_cmd(a, ADS_CMD_START1) < 0) {
        fprintf(stderr, "error: SPI transfer failed: %s\n", strerror(errno));
        goto out;
    }

    /*
     * Acquisition loop: poll DRDY, note the time it was seen low, read.
     * The kernel timestamps DRDY edges in the background; they are fetched
     * every 256 reads.  All bookkeeping happens after the run.
     */
    const double P_nom = 1.0 / rate;
    size_t nr = 0, ne = 0;
    double t_end_est = 0;
    while (!stop_requested && nr < cap) {
        if (wait_drdy(a, 0.1) < 0) {
            fprintf(stderr, "error: ADC stopped producing data (DRDY timeout)\n");
            goto out;
        }
        double t = ads_now();
        int32_t v;
        uint8_t st;
        int r = ads_read_direct(a, &v, &st);
        if (r == -1) {
            fprintf(stderr, "error: SPI transfer failed: %s\n", strerror(errno));
            goto out;
        }
        rt[nr] = t;
        rv[nr] = v;
        rok[nr] = r == 0 ? 1 : r == -3 ? 2 : 0; /* 2: no new data (re-read) */
        nr++;
        if (nr == 1)
            t_end_est = t + (cap - 1) * P_nom;
        else if (t > t_end_est)
            break; /* enough conversions have elapsed even if some were lost */
        if ((nr & 255) == 0) {
            int k;
            while ((k = ads_events(a, ev, 256)) > 0)
                for (int i = 0; i < k && ne < ecap; i++)
                    et[ne++] = ev[i].timestamp_ns * 1e-9;
        }
    }
    ads_cmd(a, ADS_CMD_STOP1);
    {
        int k;
        while ((k = ads_events(a, ev, 256)) > 0)
            for (int i = 0; i < k && ne < ecap; i++)
                et[ne++] = ev[i].timestamp_ns * 1e-9;
    }

    /*
     * Rebuild the ADC's conversion grid from the edge timestamps.  The
     * kernel occasionally misses an edge (a read overlapping the DRDY
     * pulse swallows it), so each edge's conversion number comes from the
     * time since the previous edge rather than from counting.
     */
    size_t m = 0;
    for (size_t j = 0; j < ne; j++) {
        double kk = m ? ek[m - 1] + llround((et[j] - et[m - 1]) / P_nom) : 0;
        if (m && kk == ek[m - 1])
            continue; /* glitch: two edges within half a period */
        et[m] = et[j];
        ek[m++] = kk;
    }
    double P = P_nom, a0 = 0;
    *measured = 0;
    *mismatch = 0;
    size_t nb = 0;
    if (m >= 16) {
        /* Least-squares line t = a0 + k P, then the lower envelope of the
         * residuals per block: interrupt latency only ever adds delay, and
         * the envelope also follows any slow drift (e.g. NTP slewing). */
        double sk = 0, st_ = 0, skk = 0, skt = 0;
        for (size_t j = 0; j < m; j++) {
            double kj = ek[j], tj = et[j] - et[0];
            sk += kj;
            st_ += tj;
            skk += kj * kj;
            skt += kj * tj;
        }
        double den = m * skk - sk * sk;
        P = (m * skt - sk * st_) / den;
        a0 = et[0] + (st_ - P * sk) / m;
        if (!(fabs(P * rate - 1) < 0.01)) {
            P = P_nom;
            m = 0;
        } else {
            *measured = 1.0 / P;
            nb = (m + B - 1) / B;
            env = malloc(nb * sizeof *env);
            if (!env) {
                fprintf(stderr, "error: out of memory\n");
                goto out;
            }
            for (size_t b = 0; b < nb; b++) {
                env[b] = INFINITY;
                for (size_t j = b * B; j < m && j < (b + 1) * B; j++) {
                    double r = et[j] - (a0 + ek[j] * P);
                    if (r < env[b])
                        env[b] = r;
                }
            }
        }
    } else {
        m = 0;
    }
    if (!m)
        fprintf(stderr, "warning: too few DRDY timestamps; assuming no conversions were lost\n");

    /*
     * Each read returns the latest finished conversion, i.e. the last grid
     * edge at or before the read time.  A read never precedes its edge, so
     * only a small margin is needed for the envelope's own latency.
     */
    const double M = 3e-6;
    int64_t prev = -1;
    size_t spanned = 0, j = 0;
    for (size_t i = 0; i < nr; i++) {
        if (rok[i] == 2)
            continue;
        int64_t k;
        if (m) {
            while (j + 1 < m && et[j + 1] <= rt[i])
                j++;
            size_t b = j / B;
            double e = env[b];
            if (b > 0 && env[b - 1] < e)
                e = env[b - 1];
            if (b + 1 < nb && env[b + 1] < e)
                e = env[b + 1];
            k = (int64_t)floor((rt[i] - a0 - e + M) / P);
        } else {
            k = prev + 1;
        }
        if (k <= prev) {
            (*mismatch)++; /* two reads of one conversion: keep the first */
            continue;
        }
        prev = k;
        if (k < (int64_t)SKIP)
            continue;
        size_t jx = (size_t)k - SKIP;
        if (jx >= n)
            continue;
        x[jx] = rv[i];
        ok[jx] = rok[i];
        spanned = jx + 1;
    }
    *got = (stop_requested || spanned < n) ? spanned : n;
    *repaired = repair(x, ok, *got, 1);
    rc = 0;
out:
    if (rc < 0)
        ads_cmd(a, ADS_CMD_STOP1);
    free(rv);
    free(rt);
    free(rok);
    free(et);
    free(ek);
    free(env);
    free(ok);
    return rc;
}

/* ---- 2 channels: Pi-paced one-shot conversions ------------------------ */

static int cmp_float(const void *p, const void *q)
{
    float a = *(const float *)p, b = *(const float *)q;
    return (a > b) - (a < b);
}

/* One transaction: RDATA1 (7 bytes), WREG INPMUX (3), START1 (1).
 * Writing INPMUX clears the data register, so the read must come first. */
static int read_switch_start(ads_t *a, int do_read, uint8_t next_mux, int32_t *v)
{
    uint8_t tx[11] = { ADS_CMD_RDATA1, 0, 0, 0, 0, 0, 0,
                       ADS_CMD_WREG | ADS_REG_INPMUX, 0, next_mux, ADS_CMD_START1 };
    uint8_t rx[11];
    const uint8_t *t = do_read ? tx : tx + 7;
    unsigned len = do_read ? 11 : 4;
    if (ads_xfer(a, t, rx, len) < 0)
        return -1;
    if (!do_read)
        return 0;
    *v = (int32_t)(((uint32_t)rx[2] << 24) | ((uint32_t)rx[3] << 16) | ((uint32_t)rx[4] << 8) | rx[5]);
    uint8_t sum = (uint8_t)(rx[2] + rx[3] + rx[4] + rx[5] + 0x9B);
    if (sum != rx[6] || !(rx[1] & 0x40))
        return -2;
    return 0;
}

static int acquire_2ch(ads_t *a, unsigned rate, const uint8_t mux[2], int32_t *x, size_t n,
                       size_t *got, uint32_t *repaired, uint32_t *late, double *max_late)
{
    uint8_t *ok = calloc(n * 2, 1);
    float *ch2_at = calloc(n, sizeof *ch2_at); /* channel 2 start, s after tick */
    if (!ok || !ch2_at) {
        free(ok);
        free(ch2_at);
        return -1;
    }
    memset(x, 0, n * 2 * sizeof *x);
    mlockall(MCL_CURRENT); /* best effort, see acquire_1ch */
    if (ads_wreg_verify(a, ADS_REG_MODE0, 0x40) ||               /* one-shot (pulse) */
        ads_wreg_verify(a, ADS_REG_MODE1, 0x00) ||               /* sinc1 */
        ads_wreg_verify(a, ADS_REG_MODE2, 0x80 | ADS_DR_38400)) { /* fastest settling */
        free(ok);
        free(ch2_at);
        return -1;
    }

    const double T = 1.0 / rate;
    const double LATE = 20e-6;
    double t0 = ads_now() + 0.01;
    size_t k, complete = 0; /* frames whose channel 2 has been read */
    int rc = 0;
    int32_t v;
    *late = 0;
    *max_late = 0;

    for (k = 0; k <= n && !stop_requested; k++) {
        if (k > 0 && wait_drdy(a, 0.01) < 0)
            goto timeout; /* channel 2 of frame k-1 */
        double tick = t0 + k * T;
        wait_until(tick);
        double lt = ads_now() - tick;
        if (k < n && lt > *max_late)
            *max_late = lt;
        if (k < n && lt > LATE)
            (*late)++;

        if (k == n) { /* last frame: only read channel 2 */
            int r = read_switch_start(a, 1, mux[0], &v);
            if (r == -1)
                goto spierr;
            if (r == 0) {
                x[2 * (k - 1) + 1] = v;
                ok[2 * (k - 1) + 1] = 1;
            }
            complete = n;
            break;
        }

        int r = read_switch_start(a, k > 0, mux[0], &v); /* read ch2(k-1), start ch1(k) */
        if (r == -1)
            goto spierr;
        if (k > 0 && r == 0) {
            x[2 * (k - 1) + 1] = v;
            ok[2 * (k - 1) + 1] = 1;
        }
        complete = k;
        if (wait_drdy(a, 0.01) < 0)
            goto timeout;
        ch2_at[k] = (float)(ads_now() - tick);
        r = read_switch_start(a, 1, mux[1], &v); /* read ch1(k), start ch2(k) */
        if (r == -1)
            goto spierr;
        if (r == 0) {
            x[2 * k] = v;
            ok[2 * k] = 1;
        }
    }
    goto done;

timeout:
    fprintf(stderr, "error: ADC stopped producing data (DRDY timeout)\n");
    rc = -1;
    goto done;
spierr:
    fprintf(stderr, "error: SPI transfer failed: %s\n", strerror(errno));
    rc = -1;
done:
    ads_cmd(a, ADS_CMD_STOP1);
    *got = complete;
    /* Channel 2 starts a fixed settling time after channel 1; a stall in
     * between delays it.  Flag frames more than LATE past the median. */
    if (complete > 0) {
        float *tmp = malloc(complete * sizeof *tmp);
        if (tmp) {
            memcpy(tmp, ch2_at, complete * sizeof *tmp);
            qsort(tmp, complete, sizeof *tmp, cmp_float);
            float med = tmp[complete / 2];
            for (size_t i = 0; i < complete; i++) {
                double d = ch2_at[i] - med;
                if (d > LATE)
                    (*late)++;
                if (d > *max_late)
                    *max_late = d;
            }
            free(tmp);
        }
    }
    free(ch2_at);
    *repaired = repair(x, ok, *got, 2) + repair(x + 1, ok + 1, *got, 2);
    free(ok);
    return rc;
}

/* ---- output ------------------------------------------------------------ */

static int write_file(const char *path, const file_header_t *h, const int32_t *x)
{
    char tmp[4096];
    snprintf(tmp, sizeof tmp, "%s.part", path);
    FILE *f = fopen(tmp, "wb");
    if (!f) {
        fprintf(stderr, "error: cannot create %s: %s\n", tmp, strerror(errno));
        return -1;
    }
    size_t count = (size_t)h->frames * h->channels;
    if (fwrite(h, sizeof *h, 1, f) != 1 || fwrite(x, sizeof x[0], count, f) != count ||
        fflush(f) != 0 || fsync(fileno(f)) != 0) {
        fprintf(stderr, "error: writing %s: %s\n", tmp, strerror(errno));
        fclose(f);
        unlink(tmp);
        return -1;
    }
    if (fclose(f) != 0 || rename(tmp, path) != 0) {
        fprintf(stderr, "error: finishing %s: %s\n", path, strerror(errno));
        unlink(tmp);
        return -1;
    }
    return 0;
}

int main(int argc, char **argv)
{
    const char *out = NULL;
    int inputs[2] = { 0, 1 };
    int ref_avdd = 1, filter = 1, opt;

    while ((opt = getopt(argc, argv, "o:i:r:f:h")) != -1) {
        switch (opt) {
        case 'o':
            out = optarg;
            break;
        case 'i': {
            int n = sscanf(optarg, "%d,%d", &inputs[0], &inputs[1]);
            if (n < 1 || inputs[0] < 0 || inputs[0] > 9 || inputs[1] < 0 || inputs[1] > 9) {
                fprintf(stderr, "error: -i takes AIN numbers 0-9, e.g. -i 2,3\n");
                return 1;
            }
            break;
        }
        case 'r':
            if (!strcmp(optarg, "avdd"))
                ref_avdd = 1;
            else if (!strcmp(optarg, "int"))
                ref_avdd = 0;
            else {
                fprintf(stderr, "error: -r must be avdd or int\n");
                return 1;
            }
            break;
        case 'f':
            if (optarg[0] < '1' || optarg[0] > '4' || optarg[1]) {
                fprintf(stderr, "error: -f must be 1, 2, 3 or 4\n");
                return 1;
            }
            filter = optarg[0] - '0';
            break;
        default:
            usage();
            return 1;
        }
    }
    if (argc - optind != 3) {
        usage();
        return 1;
    }

    long channels, rate;
    char *end;
    if (parse_long(argv[optind], &channels) || (channels != 1 && channels != 2)) {
        fprintf(stderr, "error: channels must be 1 or 2\n");
        return 1;
    }
    int ri = -1;
    if (!parse_long(argv[optind + 1], &rate))
        for (size_t i = 0; i < sizeof rates / sizeof rates[0]; i++)
            if (rates[i].rate == (unsigned long)rate)
                ri = (int)i;
    if (ri < 0) {
        fprintf(stderr, "error: rate must be one of 1200 2400 4800 7200 14400 19200\n");
        return 1;
    }
    if (channels == 2 && rate > MAX_RATE_2CH) {
        fprintf(stderr, "error: 2 channels support at most %d Hz: the ADS1263 has a single ADC and\n"
                        "       needs ~230 us to settle after each channel switch\n", MAX_RATE_2CH);
        return 1;
    }
    errno = 0;
    double seconds = strtod(argv[optind + 2], &end);
    if (errno || end == argv[optind + 2] || *end || !(seconds >= 0.1 && seconds <= 60.0)) {
        fprintf(stderr, "error: duration must be between 0.1 and 60 seconds\n");
        return 1;
    }
    if (channels == 2 && inputs[0] == inputs[1])
        fprintf(stderr, "warning: both channels use AIN%d\n", inputs[0]);
    if (channels == 2 && filter != 1)
        fprintf(stderr, "note: -f is ignored with 2 channels (sinc1 is used)\n");

    char defname[64];
    if (!out) {
        time_t now = time(NULL);
        strftime(defname, sizeof defname, "adSample_%Y%m%d_%H%M%S.ads", localtime(&now));
        out = defname;
    }

    size_t frames = (size_t)llround(seconds * rate);
    int32_t *x = calloc(frames * channels, sizeof *x);
    if (!x) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }

    struct sigaction sa = { .sa_handler = on_signal };
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);

    ads_t a;
    if (ads_open(&a, SPI_HZ, channels == 1) < 0)
        return 1;
    uint8_t mux[2] = { (uint8_t)(inputs[0] << 4 | ADS_AINCOM), (uint8_t)(inputs[1] << 4 | ADS_AINCOM) };
    /* REFMUX: 0x24 = AVDD/AVSS, 0x00 = internal 2.5 V (needs POWER.INTREF=1, the default) */
    if (ads_wreg_verify(&a, ADS_REG_REFMUX, ref_avdd ? 0x24 : 0x00) < 0) {
        ads_close(&a);
        return 1;
    }
    if (!ref_avdd)
        ads_sleep_us(50000); /* let the internal reference settle */

    realtime_setup();

    struct timespec rt;
    clock_gettime(CLOCK_REALTIME, &rt);
    size_t got = 0;
    uint32_t repaired = 0, late = 0, mismatch = 0;
    double measured = 0, max_late = 0;
    int rc;
    if (channels == 1)
        rc = acquire_1ch(&a, rates[ri].code, (unsigned)rate, filter, mux[0], x, frames, &got,
                         &repaired, &measured, &mismatch);
    else
        rc = acquire_2ch(&a, (unsigned)rate, mux, x, frames, &got, &repaired, &late, &max_late);
    ads_close(&a);

    if (rc < 0 || got == 0) {
        fprintf(stderr, "error: acquisition failed, no file written\n");
        return 1;
    }

    file_header_t h;
    memset(&h, 0, sizeof h);
    memcpy(h.magic, "ADS1", 4);
    h.version = 1;
    h.header_bytes = sizeof h;
    h.channels = (uint16_t)channels;
    h.sample_format = 1;
    h.sample_rate = (uint32_t)rate;
    h.frames = got;
    h.measured_rate = measured;
    h.vref = ref_avdd ? 5.0 : 2.5;
    h.start_unix_ns = (int64_t)rt.tv_sec * 1000000000LL + rt.tv_nsec;
    h.repaired = repaired;
    h.timing_errors = late;
    h.inputs[0] = (uint8_t)inputs[0];
    h.inputs[1] = channels == 2 ? (uint8_t)inputs[1] : 0xFF;
    h.ref = (uint8_t)ref_avdd;
    h.filter = (uint8_t)(channels == 1 ? filter : 1);
    if (write_file(out, &h, x) < 0)
        return 1;

    printf("%s: %zu frames x %ld ch @ %ld Hz (%.3f s)", out, got, channels, rate, (double)got / rate);
    if (measured > 0)
        printf(", ADC clock %.2f Hz", measured);
    printf("\n");

    int status = 0;
    if (got < frames) {
        printf("warning: stopped early, %zu of %zu frames recorded\n", got, frames);
        status = 3;
    }
    if (repaired) {
        printf("warning: %u sample(s) were lost and filled by interpolation (%.4f%%)\n", repaired,
               100.0 * repaired / (got * channels));
        status = 3;
    }
    if (mismatch) {
        printf("warning: %u read(s) could not be placed in time and were dropped\n", mismatch);
        status = 3;
    }
    if (late) {
        printf("warning: %u sample time(s) more than 20 us late (max %.1f us)\n", late,
               max_late * 1e6);
        status = 3;
    }
    free(x);
    return status;
}
