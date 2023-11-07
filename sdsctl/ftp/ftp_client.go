package ftp

import (
	"fmt"
	ftpclient "github.com/jlaffaye/ftp"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"io"
	"os"
	"path/filepath"
	"time"
)

type FtpClient struct {
	Host     string
	Port     string
	Username string
	Password string
	Conn     *ftpclient.ServerConn
}

func NewFtpClient(host, port, username, password string) (*FtpClient, error) {
	c, err := ftpclient.Dial(fmt.Sprintf("%s:%s", host, port), ftpclient.DialWithTimeout(5*time.Second))
	if err != nil {
		return nil, err
	}

	err = c.Login(username, password)
	if err != nil {
		return nil, err
	}

	client := &FtpClient{
		Host:     host,
		Port:     port,
		Username: username,
		Password: password,
		Conn:     c,
	}
	return client, nil
}

func (ftp *FtpClient) ListDir(dirPath string) ([]string, error) {
	exsit := ftp.IsDirExsit(dirPath)
	if !exsit {
		return nil, fmt.Errorf("no such dir:%s", dirPath)
	}
	entries, err := ftp.Conn.List(dirPath)
	if err != nil {
		return nil, err
	}
	files := make([]string, 0)
	for _, entry := range entries {
		files = append(files, entry.Name)
	}
	return files, nil
}

func (ftp *FtpClient) ListFiles(dirPath string) ([]string, error) {
	exsit := ftp.IsDirExsit(dirPath)
	if !exsit {
		return nil, fmt.Errorf("no such dir:%s", dirPath)
	}
	entries, err := ftp.Conn.List(dirPath)
	if err != nil {
		return nil, err
	}
	files := make([]string, 0)
	for _, entry := range entries {
		if entry.Type == ftpclient.EntryTypeFolder {
			tmp, _ := ftp.ListFiles(filepath.Join(dirPath, entry.Name))
			files = append(files, tmp...)
		} else if entry.Type == ftpclient.EntryTypeFile {
			files = append(files, filepath.Join(dirPath, entry.Name))
		}

	}
	return files, nil
}

func (ftp *FtpClient) Mkdir(dirPath string) error {
	exsit := ftp.IsDirExsit(dirPath)
	if exsit {
		return nil
	}
	return ftp.Conn.MakeDir(dirPath)
}

func (ftp *FtpClient) Rename(dirPath, oldName, newName string) error {
	exsit := ftp.IsDirExsit(dirPath)
	if !exsit {
		return fmt.Errorf("no such dirPath:%s", dirPath)
	}
	return ftp.Conn.Rename(oldName, newName)
}

func (ftp *FtpClient) IsDirExsit(dirPath string) bool {
	err := ftp.Conn.ChangeDir(dirPath)
	if err != nil {
		return false
	}
	return true
}

func (ftp *FtpClient) IsFileExsit(filePath string) bool {
	dirPath := filepath.Dir(filePath)
	err := ftp.Conn.ChangeDir(dirPath)
	if err != nil {
		return false
	}
	files, err := ftp.Conn.List(dirPath)
	if err != nil {
		return false
	}
	fileName := filepath.Base(filePath)
	for _, file := range files {
		if file.Name == fileName {
			return true
		}
	}
	return false
}

func (ftp *FtpClient) DeleteFile(filePath string) error {
	dirPath := filepath.Dir(filePath)
	exsit := ftp.IsDirExsit(dirPath)
	if !exsit {
		return fmt.Errorf("no such dirPath:%s", dirPath)
	}
	return ftp.Conn.Delete(filePath)
}

func (ftp *FtpClient) DeleteDir(fileDirPath string) error {
	exsit := ftp.IsDirExsit(fileDirPath)
	if !exsit {
		return fmt.Errorf("no such dirPath:%s", fileDirPath)
	}
	return ftp.Conn.RemoveDirRecur(fileDirPath)
}

func (ftp *FtpClient) UploadFile(localFilePath, targetDirPath string) error {
	exsit := ftp.IsDirExsit(targetDirPath)
	if !exsit {
		if err := ftp.Mkdir(targetDirPath); err != nil {
			return err
		}
	}
	files, err := ftp.ListDir(targetDirPath)
	if err != nil {
		return err
	}
	localFileName := filepath.Base(localFilePath)
	for _, file := range files {
		if fmt.Sprintf("%s.bak", localFileName) == file {
			ftp.DeleteFile(fmt.Sprintf("%s.bak", localFileName))
		}
		if localFileName == file {
			if err := ftp.Rename(targetDirPath, localFileName, fmt.Sprintf("%s.bak", localFileName)); err != nil {
				return err
			}
		}
	}
	file, err := os.OpenFile(localFilePath, os.O_RDONLY, os.ModePerm)
	if err != nil {
		return err
	}
	err = ftp.Conn.Stor(localFileName, file)
	if err != nil {
		ftp.Rename(targetDirPath, fmt.Sprintf("%s.bak", localFileName), localFileName)
	}
	return err
}

func (ftp *FtpClient) UploadDir(localDirPath, targetDirPath string) error {
	if !utils.Exists(localDirPath) {
		return fmt.Errorf("no such dir:%s", localDirPath)
	}
	if !ftp.IsDirExsit(targetDirPath) {
		ftp.Mkdir(targetDirPath)
	}
	files := utils.GetFiles(localDirPath)
	for _, file := range files {
		if err := ftp.UploadFile(file, targetDirPath); err != nil {
			return err
		}
	}
	return nil
}

func (ftp *FtpClient) DownloadFile(localDirPath, remoteFilePath string) error {
	if !utils.Exists(localDirPath) {
		os.MkdirAll(localDirPath, os.ModePerm)
	}
	fileName := filepath.Base(remoteFilePath)
	localFilePath := filepath.Join(localDirPath, fileName)
	file, err := os.OpenFile(localFilePath, os.O_CREATE|os.O_RDWR, os.ModePerm)
	if err != nil {
		return err
	}
	retr, err := ftp.Conn.Retr(remoteFilePath)
	if err != nil {
		return err
	}
	defer retr.Close()
	buf := make([]byte, 1024)
	for {
		n, err := retr.Read(buf)
		if err != nil && err != io.EOF {
			return err
		}
		if n == 0 {
			break
		}
		if _, err := file.Write(buf[:n]); err != nil {
			return err
		}
	}
	return nil
}

func (ftp *FtpClient) DownloadDir(localDirPath, remoteDirPath string) error {
	if utils.Exists(localDirPath) {
		os.MkdirAll(localDirPath, os.ModePerm)
	}
	if !ftp.IsDirExsit(remoteDirPath) {
		return fmt.Errorf("no such dir:%s", remoteDirPath)
	}
	files, err := ftp.ListFiles(remoteDirPath)
	if err != nil {
		return err
	}
	for _, file := range files {
		if err := ftp.DownloadFile(localDirPath, filepath.Join(remoteDirPath, file)); err != nil {
			return err
		}
	}
	return nil
}
