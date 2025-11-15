#pragma once

#include "SpringFeature.h"

namespace Spring {

class CompressionSpringFeature : public SpringFeature
{
    PROPERTY_HEADER_WITH_OVERRIDE(Spring::CompressionSpringFeature);

public:
    CompressionSpringFeature();
    ~CompressionSpringFeature() override = default;

    static void registerClass();

protected:
    SpringKind kind() const override;
};

} // namespace Spring

