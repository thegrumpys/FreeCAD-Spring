#include "SpringGui.h"

#include <Base/Console.h>

using namespace SpringGui;

void SpringGui::initModule()
{
    Base::Console().Log("Init Spring module (Gui)\n");
}

void SpringGui::finishModule()
{
    Base::Console().Log("Finish Spring module (Gui)\n");
}

extern "C" {
SpringGuiExport void initSpringGui()
{
    SpringGui::initModule();
}

SpringGuiExport void finishSpringGui()
{
    SpringGui::finishModule();
}
}

