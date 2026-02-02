#include "FlowField.h"

int main(int argc, char *argv[]) {

    auto ff = FlowField::Create(argv[1]);
    
    for(auto i = 0; i < ff->getTargetSpaceNum(); ++i)
    {
        ff->buildProjectionTexture(1024, 2048, i);
    }
    ff->preprocess();
    ff->buildTextures();
    ff->finish();

    return 0;
}
