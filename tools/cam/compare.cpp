#include "gerbertools/pcb.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

int main(int argc, char **argv) {
    if (argc != 3) return 1;
    try {
        using namespace gerbertools;
        const std::string directory = std::string(argv[1]) + "/";
        const int layers = std::stoi(argv[2]);
        pcb::CircuitBoard board(directory, "outline.gbr", "pth.drl", "npth.drl", "", 0.025);
        for (int i = 0; i < layers; ++i) {
            if (i) board.add_substrate_layer(0.25);
            board.add_copper_layer("L" + std::to_string(i) + ".gbr", 0.035);
        }
        auto builder = board.get_netlist_builder();
        std::ifstream points(directory + "logical.tsv");
        if (!points) throw std::runtime_error("Missing IPC witness coordinates");
        double x, y;
        int layer;
        size_t count = 0;
        std::string net;
        while (points >> x >> y >> layer >> net) {
            builder.net({coord::Format::from_mm(x), coord::Format::from_mm(y)}, layer, net);
            ++count;
        }
        if (!count || !points.eof()) throw std::runtime_error("Empty or invalid witness list");
        const auto findings = builder.build(0).perform_drc(0);
        std::cout << "witnesses " << count << " findings " << findings.size() << "\n";
        for (const auto &finding : findings) std::cout << finding << "\n";
        return findings.empty() ? 0 : 2;
    } catch (const std::exception &error) {
        std::cerr << error.what() << "\n";
        return 1;
    }
}
