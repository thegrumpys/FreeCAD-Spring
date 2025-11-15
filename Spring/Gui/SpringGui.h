#pragma once

#include <FCGlobal.h>

namespace SpringGui {

#ifdef SpringGui_EXPORTS
#define SpringGuiExport __FC_EXPORT
#else
#define SpringGuiExport __FC_IMPORT
#endif

void SpringGuiExport initModule();
void SpringGuiExport finishModule();

} // namespace SpringGui

extern "C" {
SpringGuiExport void initSpringGui();
SpringGuiExport void finishSpringGui();
}

