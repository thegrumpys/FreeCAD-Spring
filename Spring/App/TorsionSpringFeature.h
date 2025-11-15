#pragma once

#include "SpringFeature.h"

namespace Spring {

class TorsionSpringFeature : public SpringFeature
{
    PROPERTY_HEADER_WITH_OVERRIDE(Spring::TorsionSpringFeature);

public:
    TorsionSpringFeature();
    ~TorsionSpringFeature() override = default;

    static void registerClass();

protected:
    SpringKind kind() const override;
    TopoDS_Shape augmentShape(const TopoDS_Shape& coil) const override;
};

} // namespace Spring

