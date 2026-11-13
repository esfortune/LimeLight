CFLAGS = -O2 -Wall -Wextra

adSample: adSample.c ads1263.h
	$(CC) $(CFLAGS) -o $@ adSample.c -lm
	@echo "for real-time priority (recommended): sudo setcap cap_sys_nice,cap_ipc_lock+ep $@"

clean:
	rm -f adSample
