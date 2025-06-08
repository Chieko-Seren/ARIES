CC = gcc
CFLAGS = -O3 -mavx2 -fPIC -Wall -Wextra
LDFLAGS = -shared

# 目标文件
TARGET = libsimd_avx2.so

# 源文件
SRCS = simd_avx2.c
OBJS = $(SRCS:.c=.o)

# 默认目标
all: $(TARGET)

# 编译共享库
$(TARGET): $(OBJS)
	$(CC) $(LDFLAGS) -o $@ $^

# 编译源文件
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# 清理
clean:
	rm -f $(OBJS) $(TARGET)

# 安装
install: $(TARGET)
	cp $(TARGET) /usr/local/lib/
	ldconfig

# 卸载
uninstall:
	rm -f /usr/local/lib/$(TARGET)
	ldconfig

.PHONY: all clean install uninstall 