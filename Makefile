CC = gcc
CFLAGS = -O2 -Wall

all: tempo ops

tempo: src/sort.c
	$(CC) $(CFLAGS) -o tempo src/sort.c

ops: src/sort.c
	$(CC) $(CFLAGS) -DCONTAR -o ops src/sort.c

dados: tempo ops
	mkdir -p dados
	./tempo > dados/tempos.csv
	./ops > dados/operacoes.csv

analise:
	python3 analise/analise.py

clean:
	rm -f tempo ops

.PHONY: all dados analise clean
