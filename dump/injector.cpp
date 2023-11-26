#include <Windows.h>
#include<iostream>
BOOL InjectDLL(DWORD dwProcessId, const char* pszDLLPath)
{ 
    HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, dwProcessId);
    if (hProcess == NULL)
    { 
        return FALSE;
    }
 
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
    
    const char* pszDLLPath = R"(C:\Users\wcy\Documents\GitHub\YU-NO-Re\dump\build\Debug\dumper.dll)";  
    auto pid=GetProcessIdByName("AI5CHS.EXE");
    std::cout<<InjectDLL(pid, pszDLLPath);

    return 0;
}