package rook

import (
	"fmt"
	"testing"
)

func TestWaitRbdPoolReady(t *testing.T) {
	err := WaitRbdPoolReady("rbdpool")
	fmt.Printf("err:%+v\n", err)
}
