#pragma once

#include <Mod/Part/App/PartFeature.h>

#include <App/PropertyBool.h>
#include <App/PropertyFloat.h>


class TopoDS_Shape;

namespace Spring {

enum class SpringKind
{
    Compression,
    Extension,
    Torsion
};

class SpringFeature : public Part::Feature
{
    PROPERTY_HEADER_WITH_OVERRIDE(Spring::SpringFeature);

public:
    SpringFeature();
    ~SpringFeature() override = default;

    void onChanged(const App::Property* prop) override;
    int execute() override;

    static void registerClass();

protected:
    virtual SpringKind kind() const = 0;
    virtual TopoDS_Shape augmentShape(const TopoDS_Shape& coil) const;

    TopoDS_Shape buildCoil() const;
    double coilRadius() const;
    double wireRadius() const;
    double coilHeight() const;
    double coilPitch() const;
    bool isLeftHanded() const;

    App::PropertyFloat CoilDiameter;
    App::PropertyFloat WireDiameter;
    App::PropertyFloat Pitch;
    App::PropertyFloat ActiveCoils;
    App::PropertyBool LeftHanded;
    App::PropertyFloat StartLength;
    App::PropertyFloat EndLength;
    App::PropertyFloat ArmLength;
    App::PropertyFloat ArmAngle;
};

} // namespace Spring

