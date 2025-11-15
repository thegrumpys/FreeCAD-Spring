#include "SpringModule.h"

#include "CompressionSpringFeature.h"
#include "ExtensionSpringFeature.h"
#include "TorsionSpringFeature.h"

#include <App/Application.h>
#include <Base/Console.h>

using namespace Spring;

void Spring::initModule()
{
    Base::Console().Log("Init Spring module (App)\n");

    CompressionSpringFeature::registerClass();
    ExtensionSpringFeature::registerClass();
    TorsionSpringFeature::registerClass();
}

void Spring::finishModule()
{
    Base::Console().Log("Finish Spring module (App)\n");
}

extern "C" {
SpringAppExport void initSpring()
{
    Spring::initModule();
}

SpringAppExport void finishSpring()
{
    Spring::finishModule();
}
}

