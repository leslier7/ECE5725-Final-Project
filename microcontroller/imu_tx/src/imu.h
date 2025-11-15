#ifndef _IMU_H_
#define _IMU_H_

struct accel_data{
    double x;
    double y;
    double z;
};

struct gyro_data{
    double x;
    double y;
    double z;
};

typedef struct {
    struct accel_data accel;
    struct gyro_data gyro;
}IMU_Data;

int imu_init();

IMU_Data get_imu_data();

#endif