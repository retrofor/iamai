#include <iostream>
#include <windows.h>
#include <stdlib.h>

char* getHomeDir() {

  char homeDrive[MAX_PATH];
  char homePath[MAX_PATH];  

  strcpy(homeDrive, getenv("HOMEDRIVE"));
  strcpy(homePath, getenv("HOMEPATH"));

  char* homeDir = (char*)malloc(strlen(homeDrive) + strlen(homePath) + 1);

  strcpy(homeDir, homeDrive); 
  strcat(homeDir, homePath);

  return homeDir;

};

int main() {

  char* homeDir = getHomeDir();

  std::cout << homeDir << std::endl;

  free(homeDir);

  return 0;
}
