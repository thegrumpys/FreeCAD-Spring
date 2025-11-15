#pragma once

#include "SpringFeature.h"

namespace Spring {

class ExtensionSpringFeature : public SpringFeature
{
    PROPERTY_HEADER_WITH_OVERRIDE(Spring::ExtensionSpringFeature);

public:
    ExtensionSpringFeature();
    ~ExtensionSpringFeature() override = default;

    static void registerClass();

protected:
    SpringKind kind() const override;
    TopoDS_Shape augmentShape(const TopoDS_Shape& coil) const override;
};

} // namespace Spring

