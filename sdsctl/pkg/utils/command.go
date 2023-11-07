package utils

import (
	"bytes"
	"errors"
	"fmt"
	"github.com/urfave/cli/v2"
	"os/exec"
	"strings"
)

type Command struct {
	Cmd    string
	Params map[string]string
}

func Oneline(in []byte) string {
	str := strings.TrimSpace(string(in))
	return strings.Replace(str, "\n", ". ", -1)
}

func (comm *Command) Execute() (string, error) {
	scmd := comm.Cmd
	for k, v := range comm.Params {
		scmd += fmt.Sprintf(" %s %s ", k, v)
	}
	cmd := exec.Command("bash", "-c", scmd)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	err := cmd.Run()
	if err != nil {
		return "", errors.New(string(stderr.Bytes()))
	}
	//fmt.Println(string(stdout.Bytes()))
	return Oneline(stdout.Bytes()), nil
}

func (comm *Command) ExecuteWithPlain() ([]byte, error) {
	scmd := comm.Cmd
	for k, v := range comm.Params {
		scmd += fmt.Sprintf(" %s %s ", k, v)
	}
	cmd := exec.Command("bash", "-c", scmd)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	err := cmd.Run()
	if err != nil {
		return nil, errors.New(string(stderr.Bytes()))
	}
	//fmt.Println(string(stdout.Bytes()))
	return stdout.Bytes(), nil
}

type CommandList struct {
	Comms []*Command
}

func (cl *CommandList) Execute() error {
	for _, comm := range cl.Comms {
		if _, err := comm.Execute(); err != nil {
			return err
		}
	}
	return nil
}

// CLI parse
func ParseFlagMap(ctx *cli.Context) map[string]interface{} {
	names := ctx.LocalFlagNames()
	flags := make(map[string]interface{})
	for _, name := range names {
		flags[name] = ctx.Value(name)
	}
	return flags
}

func MergeFlags(flags, extra map[string]interface{}) map[string]interface{} {
	for k, v := range extra {
		flags[k] = v
	}
	return flags
}
