#pragma once

#include <FCGlobal.h>

namespace Spring {

#ifdef SpringApp_EXPORTS
#define SpringAppExport __FC_EXPORT
#else
#define SpringAppExport __FC_IMPORT
#endif

SpringAppExport void initModule();
SpringAppExport void finishModule();

} // namespace Spring

extern "C" {
SpringAppExport void initSpring();
SpringAppExport void finishSpring();
}

