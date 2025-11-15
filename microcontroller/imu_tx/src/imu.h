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

typedef struct __attribute__((packed)){
    float x;
    float y;
    float z;
}Sensor_DataPacked;

typedef struct __attribute__((packed)) {
    Sensor_DataPacked accel;
    Sensor_DataPacked gyro;
} IMU_DataPacked;

int imu_init();

IMU_Data get_imu_data();

IMU_DataPacked get_packed_imu_data();

#endif