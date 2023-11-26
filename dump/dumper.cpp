#include <Windows.h>
#include<vector>
#include<string>
#include<fstream>
//signed int __thiscall sub_71901720(_DWORD *this, int a2, int a3, int a4, signed int a5)
//int __usercall sub_719043E0@<eax>(int a1@<ebx>, const CHAR *lpMultiByteStr, CHAR *a3, int cbMultiByte, char a5)
 
typedef signed int (*sub_71901720_t)(DWORD *thisptr, int a2, int a3, int a4, signed int a5);
typedef int (*sub_719043E0_t)(int a1 , const CHAR *lpMultiByteStr, CHAR *a3, int cbMultiByte, char a5);
auto sub_71901720=(sub_71901720_t)((DWORD)GetModuleHandleW(L"AI5CHS.DLL")+0x1720);
auto sub_719043E0=(sub_719043E0_t)((DWORD)GetModuleHandleW(L"AI5CHS.DLL")+0x43E0);
auto dword_71908894=(DWORD)GetModuleHandleW(L"AI5CHS.DLL")+0x8894;

std::vector<std::string> strSplit(const std::string& s, const std::string  delim)
{
    std::string item;
    std::vector<std::string> tokens;

    // Copy the input string so that we can modify it
    std::string str = s;

    size_t pos = 0;
    while ((pos = str.find(delim)) != std::string::npos) {
        item = str.substr(0, pos);
        tokens.push_back(item);
        str.erase(0, pos + delim.length());
    }
    tokens.push_back(str);

    return tokens;
}
std::wstring  StringToWideString(const std::string& text, UINT encoding)
{
	std::vector<wchar_t> buffer(text.size() + 1);
	  
		if (int length = MultiByteToWideChar(encoding, 0, text.c_str(), text.size() + 1, buffer.data(), buffer.size()))
			return std::wstring(buffer.data(), length - 1);
		return {};
	 
}
 std::string WideStringToString(const std::wstring& text,UINT cp=CP_UTF8)
{
	std::vector<char> buffer((text.size() + 1) * 4);
	
		WideCharToMultiByte(cp, 0, text.c_str(), -1, buffer.data(), buffer.size(), nullptr, nullptr);
		return buffer.data();
}
int sub_71432530(unsigned __int8 *a1, char *Buffer)
{
  return sprintf(
           Buffer,
           "//%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02"
           "X%02X%02X%02X%02X%02X",
           *a1,
           a1[1],
           a1[2],
           a1[3],
           a1[4],
           a1[5],
           a1[6],
           a1[7],
           a1[8],
           a1[9],
           a1[10],
           a1[11],
           a1[12],
           a1[13],
           a1[14],
           a1[15],
           a1[16],
           a1[17],
           a1[18],
           a1[19],
           a1[20],
           a1[21],
           a1[22],
           a1[23],
           a1[24],
           a1[25],
           a1[26],
           a1[27],
           a1[28],
           a1[29],
           a1[30],
           a1[31]);
}
 
BOOL WINAPI DllMain(HINSTANCE hModule, DWORD fdwReason, LPVOID)
{
	switch (fdwReason) 
	{
	case DLL_PROCESS_ATTACH:
	{
		//#define ALL 
       	#ifndef ALL
		std::ifstream ifs(R"(C:\Users\wcy\Documents\GitHub\YU-NO-Re\unpack\vunknown.txt)");
		std::ifstream getfrommes(R"(C:\Users\wcy\Documents\GitHub\YU-NO-Re\unpack\vprefix.txt)");
		std::ofstream ofs(R"(C:\Users\wcy\Documents\GitHub\YU-NO-Re\unpack\vtext_trans2.txt)");
		#else
		std::ifstream ifs(R"(C:\Users\wcy\Documents\GitHub\YU-NO-Re\unpack\vtext.txt)");
		std::ifstream getfrommes(R"(C:\Users\wcy\Documents\GitHub\YU-NO-Re\unpack\vprefix.txt)");
		std::ofstream ofs(R"(C:\Users\wcy\Documents\GitHub\YU-NO-Re\unpack\vtext_trans.txt)");
		#endif
		std::string content((std::istreambuf_iterator<char>(ifs)),
                            (std::istreambuf_iterator<char>()));
		std::string content_getfrommes((std::istreambuf_iterator<char>(getfrommes)),
                            (std::istreambuf_iterator<char>()));
		auto strings=strSplit(content,"\n");
		auto strings_getfrommes=strSplit(content_getfrommes,"\n");
		for(auto u8str:strings){ 
			if(u8str.size()==0)continue;
			auto u16str=StringToWideString(u8str,65001);
			auto shiftjisstr=WideStringToString(u16str,932);
			wchar_t WideCharStr[1000];
			CHAR MultiByteStr[1568]; 
			auto v8 = u8str.size(); 
			int ok=0;
			 
			//这个后缀跟在shiftjis原句后面，理论上和vMES相同，然而存在部分无法对应。
			ofs.write(u8str.c_str(),u8str.size());
			ofs.write("\n",1);
			auto prefix="//000D0BFF000D0AFF0202FF0205A000FF0206A000FF0207A000FF0208A000FF00";
			strcpy(MultiByteStr,u8str.c_str());  
			strcat(MultiByteStr,prefix);  	
			auto arg3=strlen(MultiByteStr); 
			int reteax; 
			__asm{
				mov ecx,dword_71908894
				mov     ecx, [ecx]
				mov     eax, [ecx]
				mov     eax, [eax+0Ch]
				push 620h
				lea  edx,MultiByteStr
				push edx
				push arg3
				lea  edx,MultiByteStr
				push edx
				call eax
				mov reteax,eax
			}
			
			if(reteax>=0){  
				ofs.write(MultiByteStr,reteax);
				ok=1; 
			}  
			else{
				std::string u8str1="\xe3\x80\x91\xef\xbc\x88\xe7\x9b\xae\xe3\x81\xae\xe5\x89\x8d\xe3\x81\xab\xe3\x81\xaf\xe3\x82\xa2\xe3\x83\x9e\xe3\x83\xb3\xe3\x83\x80\xe3\x81\xa3\xe3\x81\xa6\xe5\xa5\xb3\xe6\x80\xa7\xe3\x81\x8c\xe3\x81\x84\xe3\x82\x8b\xe2\x80\xa5\xe2\x80\xa5\xe3\x80\x82\xef\xbc\x89";
				 
				for(int i=0;i<strings_getfrommes.size();i++){
					if(strings_getfrommes[i]==u8str){
						// if(u8str==u8str1)
						// 	MessageBoxA(0,u8str1.c_str(),"",0);
						for(int j=i+1;strings_getfrommes[j].size()&&(strings_getfrommes[j][0]=='/');j++){
							auto prefix=strings_getfrommes[j].c_str();
							
							strcpy(MultiByteStr,u8str.c_str());  
							strcat(MultiByteStr,prefix);  	
							auto arg3=strlen(MultiByteStr); 
							int reteax; 
							__asm{
								mov ecx,dword_71908894
								mov     ecx, [ecx]
								mov     eax, [ecx]
								mov     eax, [eax+0Ch]
								push 620h
								lea  edx,MultiByteStr
								push edx
								push arg3
								lea  edx,MultiByteStr
								push edx
								call eax
								mov reteax,eax
							}
							// if(u8str==u8str1)
							// 	MessageBoxA(0,prefix,std::to_string(reteax).c_str(), 0);
							if(reteax>=0){  
								ofs.write(MultiByteStr,reteax);
								ok=1;  
								break;
							}  
						}
						break;
						
					}
				}
			} 
			if(ok==0){
				ofs.write("UNKNOWN",strlen("UNKNOWN"));
			}
			ofs.write("\n\n",2); 
			//MessageBoxW(0,StringToWideString(MultiByteStr,65001).c_str(),std::to_wstring(reteax).c_str(),0);


		}
		ofs.close(); 
	} 
	break;
	 
	return TRUE;
    }
}