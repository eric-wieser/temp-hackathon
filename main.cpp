#include "MicroBit.h"

MicroBit uBit;

Serial pc(USBTX, USBRX); // tx, rx

const int N = 1;

struct {
 uint32_t time;
 int16_t x;
 int16_t y;
 int16_t z;
} data[N];

int main()
{
    // Initialise the micro:bit runtime.
    uBit.init();
    pc.baud(115200);

    //
    // Periodically read the accelerometer x and y values, and plot a
    // scaled version of this ont the display.
    //

    uBit.accelerometer.setPeriod(0);


    while(1)
    {
        if (pc.readable())
        {
            char c = pc.getc();
            uBit.display.printChar(c);
        }
        for(int i = 0; i < N; i++) {
            data[i].time = /*i == 0 ? -1 :*/ uBit.systemTime();
            data[i].x = uBit.accelerometer.getX();
            data[i].y = uBit.accelerometer.getY();
            data[i].z = uBit.accelerometer.getZ();
            uBit.sleep(1);
        }
        for(int i = 0; i < N; i++) {
            pc.printf("%d\t%d\t%d\t%d\n", data[i].time, data[i].x, data[i].y, data[i].z);
        }
    }
}