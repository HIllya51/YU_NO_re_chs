#include <Windows.h>
#include<vector>
#include<string>
#include<fstream> 
#include<InlineHook.h> 

#include"lib/Detours-4.0.1/include/detours.h"
#pragma comment(lib,"C:/Users/wcy/Documents/GitHub/YU_NO_re_chs/patch/lib/Detours-4.0.1/lib.X86/detours.lib")
auto GetCommandLineW_s=GetCommandLineW;
typedef LPWSTR (*GetCommandLineW_t)(
    VOID
    );
LPWSTR
GetCommandLineWH(
    VOID
    ){
        auto _=GetCommandLineW_s();
        auto __=new wchar_t[10000];
        wsprintfW(__,L"%s yuno JP",_);
        //MessageBoxW(0,_,L"",0);
    return __;
}
auto SetWindowTextAs=SetWindowTextA;
auto CreateWindowExA_s=CreateWindowExA;
typedef HWND (*CreateWindowExAt)(
    _In_ DWORD dwExStyle,
    _In_opt_ LPCSTR lpClassName,
    _In_opt_ LPCSTR lpWindowName,
    _In_ DWORD dwStyle,
    _In_ int X,
    _In_ int Y,
    _In_ int nWidth,
    _In_ int nHeight,
    _In_opt_ HWND hWndParent,
    _In_opt_ HMENU hMenu,
    _In_opt_ HINSTANCE hInstance,
    _In_opt_ LPVOID lpParam);
#include<thread>
HWND
CreateWindowExAh(
    _In_ DWORD dwExStyle,
    _In_opt_ LPCSTR lpClassName,
    _In_opt_ LPCSTR lpWindowName,
    _In_ DWORD dwStyle,
    _In_ int X,
    _In_ int Y,
    _In_ int nWidth,
    _In_ int nHeight,
    _In_opt_ HWND hWndParent,
    _In_opt_ HMENU hMenu,
    _In_opt_ HINSTANCE hInstance,
    _In_opt_ LPVOID lpParam){
        auto hwnd=CreateWindowExA_s(dwExStyle,lpClassName,lpWindowName,dwStyle,X,Y,nWidth,nHeight,hWndParent,hMenu,hInstance,lpParam);
        //std::thread([hwnd](){
          //  Sleep(3000);
        SetWindowTextW(hwnd,L"在世界尽头咏唱爱的少女 YU-NO          https://github.com/HIllya51/YU_NO_re_chs 制作");
        //}).detach();
        return hwnd;
    }
__declspec(dllexport) void dumy() {}

BOOL APIENTRY DllMain( HMODULE hModule,
                       DWORD  ul_reason_for_call,
                       LPVOID lpReserved
                     )
{
    switch (ul_reason_for_call)
    {
    case DLL_PROCESS_ATTACH: { 
		DetourTransactionBegin();
        DetourUpdateThread(GetCurrentThread());
        DetourAttach(&(PVOID&)GetCommandLineW_s, GetCommandLineWH); 
        DetourAttach(&(PVOID&)CreateWindowExA_s, CreateWindowExAh); 
        DetourTransactionCommit(); 

        break;
   	}
    case DLL_THREAD_ATTACH:
        break;
    case DLL_THREAD_DETACH:
        break;
    case DLL_PROCESS_DETACH:
        break;
    
    }
    return TRUE;
}