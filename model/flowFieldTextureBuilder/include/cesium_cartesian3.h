//
// Created by Yucheng Soku on 2023/3/22.
//

#ifndef FLOWFIELD_BUILDER_CESIUM_CARTESIAN3_H
#define FLOWFIELD_BUILDER_CESIUM_CARTESIAN3_H

#endif //FLOWFIELD_BUILDER_CESIUM_CARTESIAN3_H

class Cartesian3 {
public:
    double x;
    double y;
    double z;

    Cartesian3(double x = 0.0, double y = 0.0, double z = 0.0)
            : x { x }, y { y }, z { z }
    {
    }

    static double MagnitudeSquared(Cartesian3* cartesian);

    static double Magnitude(Cartesian3* cartesian);

    static Cartesian3* Normalize(Cartesian3* cartesian, Cartesian3* result);

    static Cartesian3* MultiplyComponents(Cartesian3* left, Cartesian3* right, Cartesian3* result);

    static double Dot(Cartesian3* left, Cartesian3* right);

    static Cartesian3* DivideByScalar(Cartesian3* cartesian, double scalar, Cartesian3* result);

    static Cartesian3* MultiplyByScalar(Cartesian3* cartesian, double scalar, Cartesian3* result);

    static Cartesian3* Add(Cartesian3* left, Cartesian3* right, Cartesian3* result);

    static Cartesian3* FromRadians(double longitude, double latitude, double height = 0.0, Cartesian3* result = nullptr);

    static Cartesian3* FromDegrees(double longitude, double latitude, double height = 0.0, Cartesian3* result = nullptr);
};
