package utils

import (
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"os/user"
	"path/filepath"

	"syscall"
)

// only all files exist return true, other return false
func Exists(files ...string) bool {
	for _, file := range files {
		if _, err := os.Stat(file); err != nil {
			return false
		}
	}
	return true
}

func NotExists(files ...string) bool {
	for _, file := range files {
		if _, err := os.Stat(file); err == nil {
			return false
		}
	}
	return true
}

func CreateDir(path string) {
	if !Exists(path) {
		os.MkdirAll(path, os.ModePerm)
	}
}

func IsDir(path string) bool {
	s, err := os.Stat(path)
	if err != nil {
		return false
	}
	return s.IsDir()
}

func IsFile(path string) bool {
	return !IsDir(path)
}

func GetDir(path string) string {
	return filepath.Dir(path)
}

func GetFilesUnderDir(dirPath string) []string {
	files, _ := filepath.Glob(filepath.Join(dirPath, "*"))
	return files
}

//func GetHomeDir() string {
//	if home, err := os.UserHomeDir(); err != nil {
//		return "/"
//	} else {
//		return home
//	}
//}

func GetHomeDir() string {
	currentUser, err := user.Current()
	if err != nil {
		return ""
	}

	return currentUser.HomeDir
}

func CopyFile(src, dst string) error {

	sourceFileStat, err := os.Stat(src)
	if err != nil {
		return err
	}

	if !sourceFileStat.Mode().IsRegular() {
		return fmt.Errorf("%s is not a regular file.", src)
	}

	source, err := os.Open(src)
	if err != nil {
		return err
	}
	defer source.Close()

	if Exists(dst) {
		os.RemoveAll(dst)
	}

	destination, err := os.Create(dst)
	if err != nil {
		return nil
	}
	defer destination.Close()

	buf := make([]byte, 1024)
	for {
		n, err := source.Read(buf)
		if err != nil && err != io.EOF {
			return err
		}
		if n == 0 {
			break
		}

		if _, err := destination.Write(buf[:n]); err != nil {
			return err
		}
	}
	return nil
}

func CopyFromRemoteFile(ip, localPath, remotePath string) error {
	cmd := &Command{
		Cmd: fmt.Sprintf("scp -r root@%s:%s %s", ip, remotePath, localPath),
	}
	_, err := cmd.Execute()
	return err
}

func CopyToRemoteFile(ip, localPath, remotePath string) error {
	cmd := &Command{
		Cmd: fmt.Sprintf("scp -r %s root@%s:%s", localPath, ip, remotePath),
	}
	_, err := cmd.Execute()
	return err
}

func GetFiles(dirPath string) []string {
	res := make([]string, 0)
	files, _ := ioutil.ReadDir(dirPath)
	for _, file := range files {
		if file.IsDir() {
			res = append(res, GetFiles(filepath.Join(dirPath, file.Name()))...)
		} else {
			res = append(res, filepath.Join(dirPath, file.Name()))
		}
	}
	return res
}

func Pwd() (string, error) {
	return os.Getwd()
}

func LockFile(path string) (*os.File, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	err = syscall.Flock(int(f.Fd()), syscall.LOCK_EX|syscall.LOCK_NB) // 加上排他锁，当遇到文件加锁的情况直接返回 Error
	if err != nil {
		return nil, fmt.Errorf("cannot flock file %s: %s", path, err)
	}
	return f, nil
}

func UnlockFile(file *os.File) error {
	defer file.Close()
	return syscall.Flock(int(file.Fd()), syscall.LOCK_UN)
}
