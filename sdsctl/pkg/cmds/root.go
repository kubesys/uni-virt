package cmds

import (
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/version"
	"github.com/urfave/cli/v2"
	"os"
	"runtime"
)

type AccessConfig struct {
	ip            string
	port          string
	bootStrapPort string
	CAFile        string
	CertFile      string
	KeyFile       string
}

var GlobalConfig AccessConfig

var homeDir string = func() string {
	if home, err := os.UserHomeDir(); err != nil {
		return ""
	} else {
		return home
	}
}()

func NewApp() *cli.App {
	app := cli.NewApp()
	app.Name = "sdsctl"
	app.Usage = "sdsctl, a commond-line tool to control storage for kubestack"
	app.Version = version.Version
	cli.VersionPrinter = func(c *cli.Context) {
		fmt.Printf("%s version %s\n", app.Name, app.Version)
		fmt.Printf("go version %s\n", runtime.Version())
	}
	app.Flags = []cli.Flag{}

	return app
}
