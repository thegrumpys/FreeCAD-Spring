#ifndef SPRING_WIRE_RADIUS_LAW_HPP
#define SPRING_WIRE_RADIUS_LAW_HPP

#include <Law_Function.hxx>
#include <GeomAbs_Shape.hxx>
#include <TColStd_Array1OfReal.hxx>
#include <Standard_Handle.hxx>
#include <Standard_DefineHandle.hxx>

class SpringWireRadiusLaw;
DEFINE_STANDARD_HANDLE(SpringWireRadiusLaw, Law_Function)

class SpringWireRadiusLaw : public Law_Function
{
public:
    SpringWireRadiusLaw(
        Standard_Real s0,
        Standard_Real s1,
        Standard_Real s2,
        Standard_Real s3,
        Standard_Real s4,
        Standard_Real s5,
        Standard_Real nominalScale,
        Standard_Real endScale
    );

    SpringWireRadiusLaw(
        Standard_Real s0,
        Standard_Real s1,
        Standard_Real s2,
        Standard_Real s3,
        Standard_Real s4,
        Standard_Real s5,
        Standard_Real nominalScale,
        Standard_Real endScale,
        Standard_Real firstBound,
        Standard_Real lastBound
    );

    GeomAbs_Shape Continuity() const override;
    Standard_Integer NbIntervals(const GeomAbs_Shape S) const override;
    void Intervals(TColStd_Array1OfReal& T, const GeomAbs_Shape S) const override;
    void Bounds(Standard_Real& PFirst, Standard_Real& PLast) override;

    Standard_Real Value(const Standard_Real X) override;
    void D1(const Standard_Real X, Standard_Real& F, Standard_Real& D) override;
    void D2(const Standard_Real X, Standard_Real& F, Standard_Real& D, Standard_Real& D2Val) override;

    Handle(Law_Function) Trim(
        const Standard_Real PFirst,
        const Standard_Real PLast,
        const Standard_Real Tol
    ) const override;

private:
    static Standard_Real Clamp01(Standard_Real x);

    static void SmootherStep(
        Standard_Real t,
        Standard_Real& h,
        Standard_Real& dh,
        Standard_Real& d2h
    );

    void Evaluate(
        const Standard_Real X,
        Standard_Real& F,
        Standard_Real& D,
        Standard_Real& D2Val
    ) const;

private:
    Standard_Real myS0;
    Standard_Real myS1;
    Standard_Real myS2;
    Standard_Real myS3;
    Standard_Real myS4;
    Standard_Real myS5;

    Standard_Real myNominalScale;
    Standard_Real myEndScale;

    Standard_Real myFirstBound;
    Standard_Real myLastBound;
};

#endif