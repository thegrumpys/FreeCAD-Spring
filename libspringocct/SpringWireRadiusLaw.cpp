#include "SpringWireRadiusLaw.hpp"

#include <algorithm>
#include <cmath>

SpringWireRadiusLaw::SpringWireRadiusLaw(
    Standard_Real s0,
    Standard_Real s1,
    Standard_Real s2,
    Standard_Real s3,
    Standard_Real s4,
    Standard_Real s5,
    Standard_Real nominalScale,
    Standard_Real endScale
)
    : myS0(s0),
      myS1(s1),
      myS2(s2),
      myS3(s3),
      myS4(s4),
      myS5(s5),
      myNominalScale(nominalScale),
      myEndScale(endScale),
      myFirstBound(s0),
      myLastBound(s5)
{
}

SpringWireRadiusLaw::SpringWireRadiusLaw(
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
)
    : myS0(s0),
      myS1(s1),
      myS2(s2),
      myS3(s3),
      myS4(s4),
      myS5(s5),
      myNominalScale(nominalScale),
      myEndScale(endScale),
      myFirstBound(firstBound),
      myLastBound(lastBound)
{
}

GeomAbs_Shape SpringWireRadiusLaw::Continuity() const
{
    return GeomAbs_C2;
}

Standard_Integer SpringWireRadiusLaw::NbIntervals(const GeomAbs_Shape S) const
{
    if (S <= GeomAbs_C2) {
        return 1;
    }
    return 5;
}

void SpringWireRadiusLaw::Intervals(TColStd_Array1OfReal& T, const GeomAbs_Shape S) const
{
    if (S <= GeomAbs_C2) {
        T(T.Lower())     = myFirstBound;
        T(T.Lower() + 1) = myLastBound;
        return;
    }

    const Standard_Integer i = T.Lower();
    T(i + 0) = myS0;
    T(i + 1) = myS1;
    T(i + 2) = myS2;
    T(i + 3) = myS3;
    T(i + 4) = myS4;
    T(i + 5) = myS5;
}

void SpringWireRadiusLaw::Bounds(Standard_Real& PFirst, Standard_Real& PLast)
{
    PFirst = myFirstBound;
    PLast  = myLastBound;
}

Standard_Real SpringWireRadiusLaw::Value(const Standard_Real X)
{
    Standard_Real f, d, d2;
    Evaluate(X, f, d, d2);
    return f;
}

void SpringWireRadiusLaw::D1(const Standard_Real X, Standard_Real& F, Standard_Real& D)
{
    Standard_Real d2;
    Evaluate(X, F, D, d2);
}

void SpringWireRadiusLaw::D2(const Standard_Real X, Standard_Real& F, Standard_Real& D, Standard_Real& D2Val)
{
    Evaluate(X, F, D, D2Val);
}

Handle(Law_Function) SpringWireRadiusLaw::Trim(
    const Standard_Real PFirst,
    const Standard_Real PLast,
    const Standard_Real /*Tol*/
) const
{
    Standard_Real first = std::max(PFirst, myS0);
    Standard_Real last  = std::min(PLast,  myS5);

    Handle(SpringWireRadiusLaw) trimmed =
        new SpringWireRadiusLaw(
            myS0, myS1, myS2, myS3, myS4, myS5,
            myNominalScale, myEndScale,
            first, last
        );

    return trimmed;
}

Standard_Real SpringWireRadiusLaw::Clamp01(Standard_Real x)
{
    if (x < 0.0) return 0.0;
    if (x > 1.0) return 1.0;
    return x;
}

void SpringWireRadiusLaw::SmootherStep(
    Standard_Real t,
    Standard_Real& h,
    Standard_Real& dh,
    Standard_Real& d2h
)
{
    t = Clamp01(t);

    Standard_Real t2 = t * t;
    Standard_Real t3 = t2 * t;
    Standard_Real t4 = t3 * t;
    Standard_Real t5 = t4 * t;

    h   = 6.0 * t5 - 15.0 * t4 + 10.0 * t3;
    dh  = 30.0 * t4 - 60.0 * t3 + 30.0 * t2;
    d2h = 120.0 * t3 - 180.0 * t2 + 60.0 * t;
}

void SpringWireRadiusLaw::Evaluate(
    const Standard_Real X,
    Standard_Real& F,
    Standard_Real& D,
    Standard_Real& D2Val
) const
{
    Standard_Real x = std::min(std::max(X, myFirstBound), myLastBound);

    // Region 1: bottom helix, smooth ramp nominal -> end
    if (x <= myS1) {
      Standard_Real L = myS1 - myS0;
      Standard_Real t = (L > 0.0) ? ((x - myS0) / L) : 1.0;

      Standard_Real h, dh, d2h;
      SmootherStep(t, h, dh, d2h);

      Standard_Real delta = myNominalScale - myEndScale;

      F     = myEndScale + delta * h;
      D     = (L > 0.0) ? (delta * dh / L) : 0.0;
      D2Val = (L > 0.0) ? (delta * d2h / (L * L)) : 0.0;
      return;
    }

    // Regions 2, 3, 4: constant nominal
    if (x <= myS4) {
        F = myNominalScale;
        D = 0.0;
        D2Val = 0.0;
        return;
    }

    // Region 5: top helix, smooth ramp end -> nominal
    {
      Standard_Real L = myS5 - myS4;
      Standard_Real t = (L > 0.0) ? ((x - myS4) / L) : 1.0;

      Standard_Real h, dh, d2h;
      SmootherStep(t, h, dh, d2h);

      Standard_Real delta = myEndScale - myNominalScale;

      F     = myNominalScale + delta * h;
      D     = (L > 0.0) ? (delta * dh / L) : 0.0;
      D2Val = (L > 0.0) ? (delta * d2h / (L * L)) : 0.0;
      return;
    }
}