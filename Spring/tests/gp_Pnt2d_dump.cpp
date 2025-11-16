#include <gp_Pnt2d.hxx>
#include <iostream>

int main()
{
    gp_Pnt2d point(5.0, -3.5);
    std::cout << "Created gp_Pnt2d:" << std::endl;
    std::cout << "  X = " << point.X() << std::endl;
    std::cout << "  Y = " << point.Y() << std::endl;
    return 0;
}
