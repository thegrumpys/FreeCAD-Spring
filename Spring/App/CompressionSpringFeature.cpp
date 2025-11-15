#include "CompressionSpringFeature.h"

#include <Base/Console.h>

using namespace Spring;

PROPERTY_SOURCE(Spring::CompressionSpringFeature, Spring::SpringFeature)

CompressionSpringFeature::CompressionSpringFeature()
{
    StartLength.setValue(0.0);
    EndLength.setValue(0.0);
}

void CompressionSpringFeature::registerClass()
{
    if (!CompressionSpringFeature::getClassTypeId().isDerivedFrom(SpringFeature::getClassTypeId())) {
        CompressionSpringFeature::getClassTypeId();
    }
}

SpringKind CompressionSpringFeature::kind() const
{
    return SpringKind::Compression;
}

