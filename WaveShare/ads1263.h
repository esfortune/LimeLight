/*
 * ads1263.h - minimal, dependency-free driver for the Waveshare
 * High-Precision AD HAT (TI ADS1263) on Raspberry Pi (incl. Pi 5).
 *
 * Uses only Linux kernel interfaces: spidev and the GPIO character
 * device (uAPI v2).  No wiringPi / bcm2835 / lgpio needed.
 *
 * HAT wiring (BCM numbering): RST=18, CS=22 (driven as GPIO), DRDY=17,
 * SPI0 MOSI/MISO/SCLK.  ADS1263 uses SPI mode 1.
 */
#ifndef ADS1263_H
#define ADS1263_H

#include <errno.h>
#include <fcntl.h>
#include <linux/gpio.h>
#include <linux/spi/spidev.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>

#define ADS_GPIOCHIP "/dev/gpiochip0"
#define ADS_SPIDEV   "/dev/spidev0.0"
#define ADS_PIN_RST  18
#define ADS_PIN_CS   22
#define ADS_PIN_DRDY 17

/* Commands */
#define ADS_CMD_RESET  0x06
#define ADS_CMD_START1 0x08
#define ADS_CMD_STOP1  0x0A
#define ADS_CMD_RDATA1 0x12
#define ADS_CMD_RREG   0x20
#define ADS_CMD_WREG   0x40

/* Registers */
#define ADS_REG_ID        0x00
#define ADS_REG_POWER     0x01
#define ADS_REG_INTERFACE 0x02
#define ADS_REG_MODE0     0x03
#define ADS_REG_MODE1     0x04
#define ADS_REG_MODE2     0x05
#define ADS_REG_INPMUX    0x06
#define ADS_REG_OFCAL0    0x07
#define ADS_REG_REFMUX    0x0F

/* MODE2 data-rate codes (ADC1) */
#define ADS_DR_1200  0x9
#define ADS_DR_2400  0xA
#define ADS_DR_4800  0xB
#define ADS_DR_7200  0xC
#define ADS_DR_14400 0xD
#define ADS_DR_19200 0xE
#define ADS_DR_38400 0xF

#define ADS_AINCOM 0xA

typedef struct {
    int spi_fd;
    int out_fd;   /* line request: RST, CS (outputs) */
    int in_fd;    /* line request: DRDY (input) */
    uint32_t spi_hz;
} ads_t;

static inline double ads_now(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

static inline void ads_sleep_us(long us)
{
    struct timespec ts = { us / 1000000, (us % 1000000) * 1000 };
    while (nanosleep(&ts, &ts) == -1 && errno == EINTR)
        ;
}

/* Set output lines: idx 0 = RST, idx 1 = CS */
static inline int ads_set_out(ads_t *a, int rst, int cs)
{
    struct gpio_v2_line_values v = { .bits = (uint64_t)(rst ? 1 : 0) | ((uint64_t)(cs ? 1 : 0) << 1),
                                     .mask = 3 };
    return ioctl(a->out_fd, GPIO_V2_LINE_SET_VALUES_IOCTL, &v);
}

/* Returns DRDY level (0 = data ready), or -1 on error */
static inline int ads_drdy(ads_t *a)
{
    struct gpio_v2_line_values v = { .mask = 1 };
    if (ioctl(a->in_fd, GPIO_V2_LINE_GET_VALUES_IOCTL, &v) < 0)
        return -1;
    return (int)(v.bits & 1);
}

static inline int ads_xfer(ads_t *a, const uint8_t *tx, uint8_t *rx, unsigned len)
{
    struct spi_ioc_transfer t;
    memset(&t, 0, sizeof t);
    t.tx_buf = (uintptr_t)tx;
    t.rx_buf = (uintptr_t)rx;
    t.len = len;
    t.speed_hz = a->spi_hz;
    t.bits_per_word = 8;
    return ioctl(a->spi_fd, SPI_IOC_MESSAGE(1), &t) == (int)len ? 0 : -1;
}

static inline int ads_cmd(ads_t *a, uint8_t c)
{
    uint8_t rx;
    return ads_xfer(a, &c, &rx, 1);
}

static inline int ads_wreg(ads_t *a, uint8_t reg, uint8_t val)
{
    uint8_t tx[3] = { (uint8_t)(ADS_CMD_WREG | reg), 0x00, val }, rx[3];
    return ads_xfer(a, tx, rx, 3);
}

static inline int ads_rreg(ads_t *a, uint8_t reg)
{
    uint8_t tx[3] = { (uint8_t)(ADS_CMD_RREG | reg), 0x00, 0x00 }, rx[3];
    if (ads_xfer(a, tx, rx, 3) < 0)
        return -1;
    return rx[2];
}

/* Write a register and read it back; returns 0 if it stuck. */
static inline int ads_wreg_verify(ads_t *a, uint8_t reg, uint8_t val)
{
    if (ads_wreg(a, reg, val) < 0)
        return -1;
    int r = ads_rreg(a, reg);
    if (r != val) {
        fprintf(stderr, "ads1263: register 0x%02X write 0x%02X, read back 0x%02X\n", reg, val, r);
        return -1;
    }
    return 0;
}

/*
 * Non-blocking: fetch pending DRDY falling-edge events.  Returns the
 * number fetched (0 if none) and the last event's seqno / timestamp.
 */
static inline int ads_drdy_events(ads_t *a, uint32_t *seqno, uint64_t *ts_ns)
{
    struct gpio_v2_line_event ev[32];
    int total = 0;
    for (;;) {
        ssize_t n = read(a->in_fd, ev, sizeof ev);
        if (n <= 0)
            return total;
        int k = (int)(n / sizeof ev[0]);
        *seqno = ev[k - 1].line_seqno;
        *ts_ns = ev[k - 1].timestamp_ns;
        total += k;
        if (k < 32)
            return total;
    }
}

/* Non-blocking read of pending DRDY edge events; returns count (0 if none). */
static inline int ads_events(ads_t *a, struct gpio_v2_line_event *ev, int max)
{
    ssize_t n = read(a->in_fd, ev, sizeof ev[0] * (size_t)max);
    return n > 0 ? (int)(n / (ssize_t)sizeof ev[0]) : 0;
}

static inline void ads_close(ads_t *a)
{
    if (a->out_fd >= 0) {
        ads_set_out(a, 1, 1);
        close(a->out_fd);
    }
    if (a->in_fd >= 0)
        close(a->in_fd);
    if (a->spi_fd >= 0)
        close(a->spi_fd);
    a->out_fd = a->in_fd = a->spi_fd = -1;
}

/*
 * Open SPI + GPIO, hardware-reset the chip and check the device ID.
 * CS is held low for the whole session (allowed by the ADS1263; it
 * saves a GPIO round trip per transfer).
 */
static inline int ads_open(ads_t *a, uint32_t spi_hz, int drdy_events)
{
    a->spi_fd = a->out_fd = a->in_fd = -1;
    a->spi_hz = spi_hz;

    a->spi_fd = open(ADS_SPIDEV, O_RDWR);
    if (a->spi_fd < 0) {
        fprintf(stderr, "ads1263: cannot open %s: %s (is SPI enabled? are you in group 'spi'?)\n",
                ADS_SPIDEV, strerror(errno));
        return -1;
    }
    uint8_t mode = SPI_MODE_1 | SPI_NO_CS; /* chip select is GPIO22, not CE0 */
    uint8_t bits = 8;
    if (ioctl(a->spi_fd, SPI_IOC_WR_MODE, &mode) < 0) {
        mode = SPI_MODE_1; /* fallback if controller rejects NO_CS */
        if (ioctl(a->spi_fd, SPI_IOC_WR_MODE, &mode) < 0)
            goto spifail;
    }
    if (ioctl(a->spi_fd, SPI_IOC_WR_BITS_PER_WORD, &bits) < 0 ||
        ioctl(a->spi_fd, SPI_IOC_WR_MAX_SPEED_HZ, &spi_hz) < 0)
        goto spifail;

    int chip = open(ADS_GPIOCHIP, O_RDWR);
    if (chip < 0) {
        fprintf(stderr, "ads1263: cannot open %s: %s\n", ADS_GPIOCHIP, strerror(errno));
        ads_close(a);
        return -1;
    }
    struct gpio_v2_line_request rq;
    memset(&rq, 0, sizeof rq);
    rq.offsets[0] = ADS_PIN_RST;
    rq.offsets[1] = ADS_PIN_CS;
    rq.num_lines = 2;
    rq.config.flags = GPIO_V2_LINE_FLAG_OUTPUT;
    rq.config.num_attrs = 1;
    rq.config.attrs[0].attr.id = GPIO_V2_LINE_ATTR_ID_OUTPUT_VALUES;
    rq.config.attrs[0].attr.values = 3; /* RST high, CS high */
    rq.config.attrs[0].mask = 3;
    strcpy(rq.consumer, "adSample");
    if (ioctl(chip, GPIO_V2_GET_LINE_IOCTL, &rq) < 0) {
        fprintf(stderr, "ads1263: cannot claim GPIO %d/%d: %s (in use by another program?)\n",
                ADS_PIN_RST, ADS_PIN_CS, strerror(errno));
        close(chip);
        ads_close(a);
        return -1;
    }
    a->out_fd = rq.fd;

    memset(&rq, 0, sizeof rq);
    rq.offsets[0] = ADS_PIN_DRDY;
    rq.num_lines = 1;
    rq.config.flags = GPIO_V2_LINE_FLAG_INPUT | GPIO_V2_LINE_FLAG_BIAS_PULL_UP;
    if (drdy_events) {
        /* Kernel timestamps and sequence-numbers every DRDY falling edge,
         * so lost conversions can be counted exactly. */
        rq.config.flags |= GPIO_V2_LINE_FLAG_EDGE_FALLING;
        rq.event_buffer_size = 1024;
    }
    strcpy(rq.consumer, "adSample");
    if (ioctl(chip, GPIO_V2_GET_LINE_IOCTL, &rq) < 0) {
        fprintf(stderr, "ads1263: cannot claim GPIO %d: %s\n", ADS_PIN_DRDY, strerror(errno));
        close(chip);
        ads_close(a);
        return -1;
    }
    a->in_fd = rq.fd;
    close(chip);
    if (drdy_events)
        fcntl(a->in_fd, F_SETFL, fcntl(a->in_fd, F_GETFL) | O_NONBLOCK);

    /* Hardware reset: RST low >= 4 tCLK, then wait for oscillator. */
    ads_set_out(a, 1, 1);
    ads_sleep_us(10000);
    ads_set_out(a, 0, 1);
    ads_sleep_us(10000);
    ads_set_out(a, 1, 1);
    ads_sleep_us(50000);
    ads_set_out(a, 1, 0); /* CS low for the session */
    ads_sleep_us(100);

    ads_cmd(a, ADS_CMD_STOP1);
    int id = ads_rreg(a, ADS_REG_ID);
    if (id < 0 || (id >> 5) != 0x1) {
        fprintf(stderr, "ads1263: unexpected ID register 0x%02X (ADS1263 expected); "
                        "is the HAT attached?\n", id);
        ads_close(a);
        return -1;
    }
    return 0;

spifail:
    fprintf(stderr, "ads1263: SPI setup failed: %s\n", strerror(errno));
    ads_close(a);
    return -1;
}

/*
 * Read one conversion in "direct" mode (call right after DRDY falls).
 * Frame: STATUS, D[31:24], D[23:16], D[15:8], D[7:0], CHECKSUM.
 * Returns 0 ok, -1 SPI error, -2 checksum error, -3 no-new-data.
 */
static inline int ads_read_direct(ads_t *a, int32_t *val, uint8_t *status)
{
    uint8_t tx[6] = { 0 }, rx[6];
    if (ads_xfer(a, tx, rx, 6) < 0)
        return -1;
    uint8_t sum = (uint8_t)(rx[1] + rx[2] + rx[3] + rx[4] + 0x9B);
    *status = rx[0];
    *val = (int32_t)(((uint32_t)rx[1] << 24) | ((uint32_t)rx[2] << 16) | ((uint32_t)rx[3] << 8) | rx[4]);
    if (sum != rx[5])
        return -2;
    if (!(rx[0] & 0x40))
        return -3;
    return 0;
}

#endif
