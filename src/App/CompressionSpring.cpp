#include "SpringConfig.h"

#include <Base/Console.h>

namespace Spring
{
void logTargetPlatform()
{
    Base::Console().message("Spring compression library built for %s\n", SPRING_TARGET_PLATFORM);
}
} // namespace Spring
