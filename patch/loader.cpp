#include <Windows.h>
#include<iostream>
BOOL InjectDLL(HANDLE hProcess, const char* pszDLLPath)
{ 
     
    LPVOID pRemoteBuf = VirtualAllocEx(hProcess, NULL, strlen(pszDLLPath) + 1, MEM_COMMIT, PAGE_READWRITE);
    if (pRemoteBuf == NULL)
    { 
        CloseHandle(hProcess);
        return FALSE;
    }
 
    if (!WriteProcessMemory(hProcess, pRemoteBuf, (LPVOID)pszDLLPath, strlen(pszDLLPath) + 1, NULL))
    { 
        VirtualFreeEx(hProcess, pRemoteBuf, 0, MEM_RELEASE);
        CloseHandle(hProcess);
        return FALSE;
    }
 
    HMODULE hKernel32 = GetModuleHandleA("kernel32.dll");
    LPTHREAD_START_ROUTINE pfnThreadProc = (LPTHREAD_START_ROUTINE)GetProcAddress(hKernel32, "LoadLibraryA");
    if (pfnThreadProc == NULL)
    { 
        VirtualFreeEx(hProcess, pRemoteBuf, 0, MEM_RELEASE);
        CloseHandle(hProcess);
        return FALSE;
    }
 
    HANDLE hRemoteThread = CreateRemoteThread(hProcess, NULL, 0, pfnThreadProc, pRemoteBuf, 0, NULL);
    if (hRemoteThread == NULL)
    { 
        VirtualFreeEx(hProcess, pRemoteBuf, 0, MEM_RELEASE);
        CloseHandle(hProcess);
        return FALSE;
    }
 
    WaitForSingleObject(hRemoteThread, INFINITE);
 
    VirtualFreeEx(hProcess, pRemoteBuf, 0, MEM_RELEASE);
    CloseHandle(hRemoteThread);
    CloseHandle(hProcess);

    return TRUE;
}
#include<string>
#include <tlhelp32.h>

DWORD GetProcessIdByName(const char* processName) {
    DWORD processId = 0;
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot != INVALID_HANDLE_VALUE) {
        PROCESSENTRY32 processEntry;
        processEntry.dwSize = sizeof(PROCESSENTRY32);
        if (Process32First(snapshot, &processEntry)) {
            do {
                if (strcmp(processEntry.szExeFile, processName) == 0) {
                    processId = processEntry.th32ProcessID;
                    break;
                }
            } while (Process32Next(snapshot, &processEntry));
        }
        CloseHandle(snapshot);
    }
    return processId;
}

int main(int argc)
{
    STARTUPINFOW si;
    PROCESS_INFORMATION pi;

    ZeroMemory( &si, sizeof(si) );
    si.cb = sizeof(si);
    ZeroMemory( &pi, sizeof(pi) );
    CreateProcessW( L".\\Game.exe",   // No module name (use command line)
        L".\\Game.exe yuno JP",
        NULL,           // Process handle not inheritable
        NULL,           // Thread handle not inheritable
        FALSE,          // Set handle inheritance to FALSE
        CREATE_SUSPENDED,              // No creation flags
        NULL,           // Use parent's environment block
        NULL,           // Use parent's starting directory 
        &si,            // Pointer to STARTUPINFO structure
        &pi );           // Pointer to PROCESS_INFORMATION structure
    char path[1000]={0};
    char current[1000]={0};
    GetCurrentDirectoryA(1000,current);
    sprintf(path,"%s\\patch.dll",current);
    std::cout<<path<<"\n"; 
     
    std::cout<<InjectDLL(  pi.hProcess,path);
    ResumeThread(pi.hThread);
    return 0;
}