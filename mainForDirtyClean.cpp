#include "SortController.h"
#include "algorithms/SortAlgo.h"
#include "settings/Interface.h"
#include "settings/settings.h"
#include "algorithms/Utils.h"
#include <iostream>
#include <random>

using namespace std;

// All global vectors and variables are retained as they might be used
// internally by SortController, SortGame, or the DirtyClean4 algorithm.

vector<vector<int>> buckets;

vector<ll> A;             // list of objects
vector<int> preds;        // list of predictions
vector<int> ranking;      // list of true ranking
vector<vector<bool>> rel; // relation matrix

vector<int> sorted; // sorted list of objects
vector<int> uni_preds, indexes; // uniquified predictions and indexes
vector<int> output_rank;    // output ranking

// for tim sort
vector<int> leftTemp, rightTemp;

// for OESM
vector<int> odd_l, odd_r, even_l, even_r, merged;

// for Kim Cook
vector<int> ordered, unordered1, unordered2;

// for Both
vector<int> p_to_A, inserted;
vector<int> left_sorted, right_sorted, left_bef, right_aft, insert_par, combine;
// vector<int> left_order, right_order, left_weight, right_weight

vector<Node *> ai_to_node;
vector<int> li, ri;

// for DirtyClean2
vector<int> shuffledA;

// for ScapegoatTree
vector<Node*> nodes;

// for localshuffle
vector<int> segs;

vector<vector<vector<ll>>> results;

// MODIFICATION START: Only include DirtyClean4
vector <string> names{
    "DirtyClean4",
};
vector <SortAlgorithm*> algos {
    new DirtyClean4(),
};
// MODIFICATION END

void main_objects(int n, int REP, string setting)
{
    int num_algo = algos.size();
    // cout << "n = " << n << endl;
    int gap = 20;
    for (int i = 0; i <= gap; i++)
    {
        // cerr << "start error = " << error << endl;
        double start_time = get_time();
        double error_rate = i / (double)gap;

        vector<vector<ll>> result;
        result.resize(num_algo);
        for (int i = 0; i < REP; i++)
        {
            SortGame *game = new SortGame();

            if (setting == "exact")
                defaultrelation(game, n);
            else if (setting == "decay2" || setting == "decay")
                decayobject2(game, n, error_rate);
            else if (setting == "decay2_1000")
                decayobject2_1000(game, n, error_rate);
            else if (setting == "local" || setting == "class") {
                int seg = error_rate * n; //for stability when error_rate = 0
                if (seg == 0)
                    seg = 1;
                localshuffleobject(game, n, seg);
            }
            else {
                cerr << "wrong setting" << endl;
                exit(0);
            }

            SortController controller(game);
            for (int i = 0; i < num_algo; i++)
                controller.addAlgorithm(algos[i], names[i]);

            vector<ll> tmp = controller.runGame(i % 20 == 0);
            for (int j = 0; j < num_algo; j++)
                result[j].push_back(tmp[j]);
        }
        results.push_back(result);
        // print result
        for (int d1 = 0; d1 < num_algo; d1++) {
            cerr << "(";
            for (int d2 = 0; d2 < num_algo; d2 ++)
                cerr << result[d1][d2] << " ";
            cerr << ")";
        }
        cerr << endl;
        cerr << "finished error = " << error_rate << " time spend: " << get_time() - start_time << endl;
    }
}

void main2(int rep)
{ // for country populations
    
    int num_algo = algos.size();

    for (int old = 0; old <= 60; old++)
    {
        cerr << "old" << old << endl;
        vector<vector<ll>> result;
        result.resize(num_algo);

        SortGame *game = new SortGame();
        countrypopulation(game, old);

        for (int i = 0; i < rep; i++)
        {
            SortController controller(game);
            for (int i_algo = 0; i_algo < num_algo; i_algo ++)
                controller.addAlgorithm(algos[i_algo], names[i_algo]);

            vector<ll> tmp = controller.runGame(i == 0);
            for (int j = 0; j < num_algo; j++)
                result[j].push_back(tmp[j]);
        }
        results.push_back(result);
    }
}

void main_relational(int n, int REP, string setting)
{
    int num_algo = algos.size();
    int gap = 20;
    for (int i = 0; i <= gap; i++)
    {
        double start_time = get_time();
        double error_rate = i / (double)gap;

        // error_rate = rand() / (double)RAND_MAX;
        // cerr << "start error = " << error_rate << endl;

        vector<vector<ll>> result;
        result.resize(num_algo);
        int REP_ALGO = 5;
        assert(REP >= REP_ALGO);
        for (int i = 0; i < REP / REP_ALGO; i++)
        {
            SortGame *game = new SortGame();
            if (setting == "goodbad" || setting == "gb" || setting == "good-dominating")
                Goodbadrelation(game, n, error_rate);
            else if (setting == "badgood" || setting == "bg" || setting == "bad-dominating")
                Badgoodrelation(game, n, error_rate);
            else
            {
                cerr << "wrong setting" << endl;
                exit(0);
            }

            SortController controller(game);
            for (int i = 0; i < num_algo; i++)
                controller.addAlgorithm(algos[i], names[i]);
            for (int rep_algo = 1; rep_algo <= REP_ALGO; rep_algo++) {
                game->ReltoRank();
                vector<ll> tmp = controller.runGame(i == 0);
                for (int j = 0; j < num_algo; j++)
                    result[j].push_back(tmp[j]);
            }
        }

        // game.output_rank();
        results.push_back(result);
        cerr << "finished error = " << error_rate << " time spend: " << get_time() - start_time << endl;
    }
}

int main()
{
    srand(19260817);
    assert(names.size() == algos.size());
    // main2();
    string pred_type, setting;
    int n = 0, rep = 0;
    cin >> pred_type >> setting;
    printf("Going to run: %s", pred_type.c_str());
    if (pred_type == "positional" || pred_type == "p")
    {
        if (setting == "country" || setting == "c")
        {
            n = 263;
            cin >> rep;
            // The logic to conditionally add LIS_small, BothAlgo_small, and DirtyClean4 is REMOVED
            // because we are forcing only DirtyClean4 globally.
            main2(rep);
        }
        else
        {
            cin >> n >> rep;
            // The logic to conditionally add LIS_small, BothAlgo_small, and DirtyClean4 is REMOVED
            // because we are forcing only DirtyClean4 globally.
            main_objects(n, rep, setting);
        }
    }
    else if (pred_type == "relational" || pred_type == "r" || pred_type == "dirty")
    {
        // The logic to conditionally add other algorithms is REMOVED
        // because we are forcing only DirtyClean4 globally.
        
        cin >> n >> rep;
        main_relational(n, rep, setting);
    }
    
    
    // turn n, rep into string
    string n_str = to_string(n);
    string rep_str = to_string(rep);

    int num_algo = algos.size();
    
    output_to_file(names, results, pred_type + "_" + setting + "_" + n_str + "_" + rep_str);
    return 0;
}