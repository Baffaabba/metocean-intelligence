model_cards = dict(
    nhitsm={
        "Abstract": (
            "The N-HiTS_M incorporates hierarchical interpolation and multi-rate data sampling "
            "techniques. It assembles its predictions sequentially, selectively emphasizing "
            "components with different frequencies and scales, while decomposing the input signal "
            " and synthesizing the forecast [Cristian Challu, Kin G. Olivares, Boris N. Oreshkin, "
            "Federico Garza, Max Mergenthaler-Canseco, Artur Dubrawski. N-HiTS: Neural "
            "Hierarchical Interpolation for Time Series Forecasting, Submitted working paper.]"
            "(https://arxiv.org/abs/2201.12886)"
        ),
        "Intended use": (
            "The N-HiTS_M model specializes in monthly long-horizon forecasting by improving "
            "accuracy and reducing the training time and memory requirements of the model."
        ),
        "Secondary use": (
            "The interpretable predictions of the model produce a natural frequency time "
            "series signal decomposition."
        ),
        "Limitations": (
            "The transferability across different frequencies has not yet been tested, it is "
            "advisable to restrict the use of N-HiTS_{M} to monthly data were it was pre-trained. "
            "This model purely autorregresive, transferability of models with exogenous variables "
            "is yet to be done."
        ),
        "Training data": (
            "N-HiTS_M was trained on 48,000 monthly series from the M4 competition "
            "[Spyros  Makridakis,  Evangelos  Spiliotis, and  Vassilios Assimakopoulos. The "
            " M4  competition: 100,000  time  series and 61 forecasting methods. International "
            "Journal of Forecasting, 36(1):54–74, 2020. ISSN  0169-2070.]"
            "(https://www.sciencedirect.com/science/article/pii/S0169207019301128)"
        ),
        "Citation Info": (
            "@article{challu2022nhits,\n "
            "author    = {Cristian Challu and \n"
            "              Kin G. Olivares and \n"
            "              Boris N. Oreshkin and \n"
            "              Federico Garza and \n"
            "              Max Mergenthaler and \n"
            "              Artur Dubrawski}, \n "
            "title     = {N-HiTS: Neural Hierarchical Interpolation for Time Series Forecasting},\n "
            "journal   = {Computing Research Repository},\n "
            "volume    = {abs/2201.12886},\n "
            "year      = {2022},\n "
            "url       = {https://arxiv.org/abs/2201.12886},\n "
            "eprinttype = {arXiv},\n "
            "eprint    = {2201.12886},\n "
            "biburl    = {https://dblp.org/rec/journals/corr/abs-2201-12886.bib}\n}"
        ),
    },
    nhitsh={
        "Abstract": (
            "The N-HiTS_{H} incorporates hierarchical interpolation and multi-rate data sampling "
            "techniques. It assembles its predictions sequentially, selectively emphasizing "
            "components with different frequencies and scales, while decomposing the input signal "
            " and synthesizing the forecast [Cristian Challu, Kin G. Olivares, Boris N. Oreshkin, "
            "Federico Garza, Max Mergenthaler-Canseco, Artur Dubrawski. N-HiTS: Neural "
            "Hierarchical Interpolation for Time Series Forecasting, Submitted working paper.]"
            "(https://arxiv.org/abs/2201.12886)"
        ),
        "Intended use": (
            "The N-HiTS_{H} model specializes in hourly long-horizon forecasting by improving "
            "accuracy and reducing the training time and memory requirements of the model."
        ),
        "Secondary use": (
            "The interpretable predictions of the model produce a natural frequency time "
            "series signal decomposition."
        ),
        "Limitations": (
            "The transferability across different frequencies has not yet been tested, it is "
            "advisable to restrict the use of N-HiTS_{H} to hourly data were it was pre-trained. "
            "This model purely autorregresive, transferability of models with exogenous variables "
            "is yet to be done."
        ),
        "Training data": (
            "N-HiTS_{H} was trained on 414 hourly series from the M4 competition "
            "[Spyros  Makridakis,  Evangelos  Spiliotis, and  Vassilios Assimakopoulos. The "
            " M4  competition: 100,000  time  series and 61 forecasting methods. International "
            "Journal of Forecasting, 36(1):54–74, 2020. ISSN  0169-2070.]"
            "(https://www.sciencedirect.com/science/article/pii/S0169207019301128)"
        ),
        "Citation Info": (
            "@article{challu2022nhits,\n "
            "author    = {Cristian Challu and \n"
            "              Kin G. Olivares and \n"
            "              Boris N. Oreshkin and \n"
            "              Federico Garza and \n"
            "              Max Mergenthaler and \n"
            "              Artur Dubrawski}, \n "
            "title     = {N-HiTS: Neural Hierarchical Interpolation for Time Series Forecasting},\n "
            "journal   = {Computing Research Repository},\n "
            "volume    = {abs/2201.12886},\n "
            "year      = {2022},\n "
            "url       = {https://arxiv.org/abs/2201.12886},\n "
            "eprinttype = {arXiv},\n "
            "eprint    = {2201.12886},\n "
            "biburl    = {https://dblp.org/rec/journals/corr/abs-2201-12886.bib}\n}"
        ),
    },
    nhitsd={
        "Abstract": (
            "The N-HiTS_D incorporates hierarchical interpolation and multi-rate data sampling "
            "techniques. It assembles its predictions sequentially, selectively emphasizing "
            "components with different frequencies and scales, while decomposing the input signal "
            " and synthesizing the forecast [Cristian Challu, Kin G. Olivares, Boris N. Oreshkin, "
            "Federico Garza, Max Mergenthaler-Canseco, Artur Dubrawski. N-HiTS: Neural "
            "Hierarchical Interpolation for Time Series Forecasting, Submitted working paper.]"
            "(https://arxiv.org/abs/2201.12886)"
        ),
        "Intended use": (
            "The N-HiTS_D model specializes in daily long-horizon forecasting by improving "
            "accuracy and reducing the training time and memory requirements of the model."
        ),
        "Secondary use": (
            "The interpretable predictions of the model produce a natural frequency time "
            "series signal decomposition."
        ),
        "Limitations": (
            "The transferability across different frequencies has not yet been tested, it is "
            "advisable to restrict the use of N-HiTS_D to daily data were it was pre-trained. "
            "This model purely autorregresive, transferability of models with exogenous variables "
            "is yet to be done."
        ),
        "Training data": (
            "N-HiTS_D was trained on 4,227 daily series from the M4 competition "
            "[Spyros  Makridakis,  Evangelos  Spiliotis, and  Vassilios Assimakopoulos. The "
            " M4  competition: 100,000  time  series and 61 forecasting methods. International "
            "Journal of Forecasting, 36(1):54–74, 2020. ISSN  0169-2070.]"
            "(https://www.sciencedirect.com/science/article/pii/S0169207019301128)"
        ),
        "Citation Info": (
            "@article{challu2022nhits,\n "
            "author    = {Cristian Challu and \n"
            "              Kin G. Olivares and \n"
            "              Boris N. Oreshkin and \n"
            "              Federico Garza and \n"
            "              Max Mergenthaler and \n"
            "              Artur Dubrawski}, \n "
            "title     = {N-HiTS: Neural Hierarchical Interpolation for Time Series Forecasting},\n "
            "journal   = {Computing Research Repository},\n "
            "volume    = {abs/2201.12886},\n "
            "year      = {2022},\n "
            "url       = {https://arxiv.org/abs/2201.12886},\n "
            "eprinttype = {arXiv},\n "
            "eprint    = {2201.12886},\n "
            "biburl    = {https://dblp.org/rec/journals/corr/abs-2201-12886.bib}\n}"
        ),
    },
    nhitsy={
        "Abstract": (
            "The N-HiTS_Y incorporates hierarchical interpolation and multi-rate data sampling "
            "techniques. It assembles its predictions sequentially, selectively emphasizing "
            "components with different frequencies and scales, while decomposing the input signal "
            " and synthesizing the forecast [Cristian Challu, Kin G. Olivares, Boris N. Oreshkin, "
            "Federico Garza, Max Mergenthaler-Canseco, Artur Dubrawski. N-HiTS: Neural "
            "Hierarchical Interpolation for Time Series Forecasting, Submitted working paper.]"
            "(https://arxiv.org/abs/2201.12886)"
        ),
        "Intended use": (
            "The N-HiTS_Y model specializes in yearly long-horizon forecasting by improving "
            "accuracy and reducing the training time and memory requirements of the model."
        ),
        "Secondary use": (
            "The interpretable predictions of the model produce a natural frequency time "
            "series signal decomposition."
        ),
        "Limitations": (
            "The transferability across different frequencies has not yet been tested, it is "
            "advisable to restrict the use of N-HiTS_Y to yearly data were it was pre-trained. "
            "This model purely autorregresive, transferability of models with exogenous variables "
            "is yet to be done."
        ),
        "Training data": (
            "N-HiTS_{H} was trained on 23,000 yearly series from the M4 competition "
            "[Spyros  Makridakis,  Evangelos  Spiliotis, and  Vassilios Assimakopoulos. The "
            " M4  competition: 100,000  time  series and 61 forecasting methods. International "
            "Journal of Forecasting, 36(1):54–74, 2020. ISSN  0169-2070.]"
            "(https://www.sciencedirect.com/science/article/pii/S0169207019301128)"
        ),
        "Citation Info": (
            "@article{challu2022nhits,\n "
            "author    = {Cristian Challu and \n"
            "              Kin G. Olivares and \n"
            "              Boris N. Oreshkin and \n"
            "              Federico Garza and \n"
            "              Max Mergenthaler and \n"
            "              Artur Dubrawski}, \n "
            "title     = {N-HiTS: Neural Hierarchical Interpolation for Time Series Forecasting},\n "
            "journal   = {Computing Research Repository},\n "
            "volume    = {abs/2201.12886},\n "
            "year      = {2022},\n "
            "url       = {https://arxiv.org/abs/2201.12886},\n "
            "eprinttype = {arXiv},\n "
            "eprint    = {2201.12886},\n "
            "biburl    = {https://dblp.org/rec/journals/corr/abs-2201-12886.bib}\n}"
        ),
    },
    nbeatsm={
        "Abstract": (
            "The N-BEATS_M models is a model based on a deep stack multi-layer percentrons connected"
            "with doubly residual connections. The model combines a multi-step forecasting strategy "
            "with projections unto piecewise functions for its generic version or polynomials and "
            "harmonics for its interpretable version. [Boris N. Oreshkin, Dmitri Carpov, Nicolas "
            "Chapados, Yoshua Bengio. N-BEATS: Neural basis expansion analysis for interpretable "
            "time series forecasting. 8th International Conference on Learning Representations, "
            "ICLR 2020.](https://arxiv.org/abs/1905.10437)"
        ),
        "Intended use": (
            "The N-BEATS_M is an efficient univariate forecasting model specialized in monthly "
            "data, that uses the multi-step forecasting strategy."
        ),
        "Secondary use": (
            "The interpretable variant of N-BEATSi_M produces a trend and seasonality "
            "decomposition."
        ),
        "Limitations": (
            "The transferability across different frequencies has not yet been tested, it is "
            "advisable to restrict the use of N-BEATS_M to monthly data were it was pre-trained."
            "This model purely autorregresive, transferability of models with exogenous variables "
            "is yet to be done."
        ),
        "Training data": (
            "N-BEATS_M was trained on 48,000 monthly series from the M4 competition "
            "[Spyros  Makridakis,  Evangelos  Spiliotis, and  Vassilios Assimakopoulos. The "
            " M4  competition: 100,000  time  series and 61 forecasting methods. International "
            "Journal of Forecasting, 36(1):54–74, 2020. ISSN  0169-2070.]"
            "(https://www.sciencedirect.com/science/article/pii/S0169207019301128)"
        ),
        "Citation Info": (
            "@inproceedings{oreshkin2020nbeats,\n "
            "author    = {Boris N. Oreshkin and \n"
            "              Dmitri Carpov and \n"
            "              Nicolas Chapados and\n"
            "              Yoshua Bengio},\n "
            "title     = {{N-BEATS:} Neural basis expansion analysis for interpretable time series forecasting},\n "
            "booktitle = {8th International Conference on Learning Representations, {ICLR} 2020},\n "
            "year      = {2020},\n "
            "url       = {https://openreview.net/forum?id=r1ecqn4YwB}\n }"
        ),
    },
    nbeatsh={
        "Abstract": (
            "The N-BEATS_H models is a model based on a deep stack multi-layer percentrons connected"
            "with doubly residual connections. The model combines a multi-step forecasting strategy "
            "with projections unto piecewise functions for its generic version or polynomials and "
            "harmonics for its interpretable version. [Boris N. Oreshkin, Dmitri Carpov, Nicolas "
            "Chapados, Yoshua Bengio. N-BEATS: Neural basis expansion analysis for interpretable "
            "time series forecasting. 8th International Conference on Learning Representations, "
            "ICLR 2020.](https://arxiv.org/abs/1905.10437)"
        ),
        "Intended use": (
            "The N-BEATS_H is an efficient univariate forecasting model specialized in hourly "
            "data, that uses the multi-step forecasting strategy."
        ),
        "Secondary use": (
            "The interpretable variant of N-BEATSi_H produces a trend and seasonality "
            "decomposition."
        ),
        "Limitations": (
            "The transferability across different frequencies has not yet been tested, it is "
            "advisable to restrict the use of N-BEATS_H to hourly data were it was pre-trained."
            "This model purely autorregresive, transferability of models with exogenous variables "
            "is yet to be done."
        ),
        "Training data": (
            "N-BEATS_H was trained on 414 hourly series from the M4 competition "
            "[Spyros  Makridakis,  Evangelos  Spiliotis, and  Vassilios Assimakopoulos. The "
            " M4  competition: 100,000  time  series and 61 forecasting methods. International "
            "Journal of Forecasting, 36(1):54–74, 2020. ISSN  0169-2070.]"
            "(https://www.sciencedirect.com/science/article/pii/S0169207019301128)"
        ),
        "Citation Info": (
            "@inproceedings{oreshkin2020nbeats,\n "
            "author    = {Boris N. Oreshkin and \n"
            "              Dmitri Carpov and \n"
            "              Nicolas Chapados and\n"
            "              Yoshua Bengio},\n "
            "title     = {{N-BEATS:} Neural basis expansion analysis for interpretable time series forecasting},\n "
            "booktitle = {8th International Conference on Learning Representations, {ICLR} 2020},\n "
            "year      = {2020},\n "
            "url       = {https://openreview.net/forum?id=r1ecqn4YwB}\n }"
        ),
    },
    nbeatsd={
        "Abstract": (
            "The N-BEATS_D models is a model based on a deep stack multi-layer percentrons connected"
            "with doubly residual connections. The model combines a multi-step forecasting strategy "
            "with projections unto piecewise functions for its generic version or polynomials and "
            "harmonics for its interpretable version. [Boris N. Oreshkin, Dmitri Carpov, Nicolas "
            "Chapados, Yoshua Bengio. N-BEATS: Neural basis expansion analysis for interpretable "
            "time series forecasting. 8th International Conference on Learning Representations, "
            "ICLR 2020.](https://arxiv.org/abs/1905.10437)"
        ),
        "Intended use": (
            "The N-BEATS_D is an efficient univariate forecasting model specialized in hourly "
            "data, that uses the multi-step forecasting strategy."
        ),
        "Secondary use": (
            "The interpretable variant of N-BEATSi_D produces a trend and seasonality "
            "decomposition."
        ),
        "Limitations": (
            "The transferability across different frequencies has not yet been tested, it is "
            "advisable to restrict the use of N-BEATS_D to daily data were it was pre-trained."
            "This model purely autorregresive, transferability of models with exogenous variables "
            "is yet to be done."
        ),
        "Training data": (
            "N-BEATS_D was trained on 4,227 daily series from the M4 competition "
            "[Spyros  Makridakis,  Evangelos  Spiliotis, and  Vassilios Assimakopoulos. The "
            " M4  competition: 100,000  time  series and 61 forecasting methods. International "
            "Journal of Forecasting, 36(1):54–74, 2020. ISSN  0169-2070.]"
            "(https://www.sciencedirect.com/science/article/pii/S0169207019301128)"
        ),
        "Citation Info": (
            "@inproceedings{oreshkin2020nbeats,\n "
            "author    = {Boris N. Oreshkin and \n"
            "              Dmitri Carpov and \n"
            "              Nicolas Chapados and\n"
            "              Yoshua Bengio},\n "
            "title     = {{N-BEATS:} Neural basis expansion analysis for interpretable time series forecasting},\n "
            "booktitle = {8th International Conference on Learning Representations, {ICLR} 2020},\n "
            "year      = {2020},\n "
            "url       = {https://openreview.net/forum?id=r1ecqn4YwB}\n }"
        ),
    },
    nbeatsw={
        "Abstract": (
            "The N-BEATS_W models is a model based on a deep stack multi-layer percentrons connected"
            "with doubly residual connections. The model combines a multi-step forecasting strategy "
            "with projections unto piecewise functions for its generic version or polynomials and "
            "harmonics for its interpretable version. [Boris N. Oreshkin, Dmitri Carpov, Nicolas "
            "Chapados, Yoshua Bengio. N-BEATS: Neural basis expansion analysis for interpretable "
            "time series forecasting. 8th International Conference on Learning Representations, "
            "ICLR 2020.](https://arxiv.org/abs/1905.10437)"
        ),
        "Intended use": (
            "The N-BEATS_W is an efficient univariate forecasting model specialized in weekly "
            "data, that uses the multi-step forecasting strategy."
        ),
        "Secondary use": (
            "The interpretable variant of N-BEATSi_W produces a trend and seasonality "
            "decomposition."
        ),
        "Limitations": (
            "The transferability across different frequencies has not yet been tested, it is "
            "advisable to restrict the use of N-BEATS_W to weekly data were it was pre-trained."
            "This model purely autorregresive, transferability of models with exogenous variables "
            "is yet to be done."
        ),
        "Training data": (
            "N-BEATS_W was trained on 359 weekly series from the M4 competition "
            "[Spyros  Makridakis,  Evangelos  Spiliotis, and  Vassilios Assimakopoulos. The "
            " M4  competition: 100,000  time  series and 61 forecasting methods. International "
            "Journal of Forecasting, 36(1):54–74, 2020. ISSN  0169-2070.]"
            "(https://www.sciencedirect.com/science/article/pii/S0169207019301128)"
        ),
        "Citation Info": (
            "@inproceedings{oreshkin2020nbeats,\n "
            "author    = {Boris N. Oreshkin and \n"
            "              Dmitri Carpov and \n"
            "              Nicolas Chapados and\n"
            "              Yoshua Bengio},\n "
            "title     = {{N-BEATS:} Neural basis expansion analysis for interpretable time series forecasting},\n "
            "booktitle = {8th International Conference on Learning Representations, {ICLR} 2020},\n "
            "year      = {2020},\n "
            "url       = {https://openreview.net/forum?id=r1ecqn4YwB}\n }"
        ),
    },
    nbeatsy={
        "Abstract": (
            "The N-BEATS_Y models is a model based on a deep stack multi-layer percentrons connected"
            "with doubly residual connections. The model combines a multi-step forecasting strategy "
            "with projections unto piecewise functions for its generic version or polynomials and "
            "harmonics for its interpretable version. [Boris N. Oreshkin, Dmitri Carpov, Nicolas "
            "Chapados, Yoshua Bengio. N-BEATS: Neural basis expansion analysis for interpretable "
            "time series forecasting. 8th International Conference on Learning Representations, "
            "ICLR 2020.](https://arxiv.org/abs/1905.10437)"
        ),
        "Intended use": (
            "The N-BEATS_Y is an efficient univariate forecasting model specialized in hourly "
            "data, that uses the multi-step forecasting strategy."
        ),
        "Secondary use": (
            "The interpretable variant of N-BEATSi_Y produces a trend and seasonality "
            "decomposition."
        ),
        "Limitations": (
            "The transferability across different frequencies has not yet been tested, it is "
            "advisable to restrict the use of N-BEATS_Y to yearly data were it was pre-trained."
            "This model purely autorregresive, transferability of models with exogenous variables "
            "is yet to be done."
        ),
        "Training data": (
            "N-BEATS_Y was trained on 23,000 yearly series from the M4 competition "
            "[Spyros  Makridakis,  Evangelos  Spiliotis, and  Vassilios Assimakopoulos. The "
            " M4  competition: 100,000  time  series and 61 forecasting methods. International "
            "Journal of Forecasting, 36(1):54–74, 2020. ISSN  0169-2070.]"
            "(https://www.sciencedirect.com/science/article/pii/S0169207019301128)"
        ),
        "Citation Info": (
            "@inproceedings{oreshkin2020nbeats,\n "
            "author    = {Boris N. Oreshkin and \n"
            "              Dmitri Carpov and \n"
            "              Nicolas Chapados and\n"
            "              Yoshua Bengio},\n "
            "title     = {{N-BEATS:} Neural basis expansion analysis for interpretable time series forecasting},\n "
            "booktitle = {8th International Conference on Learning Representations, {ICLR} 2020},\n "
            "year      = {2020},\n "
            "url       = {https://openreview.net/forum?id=r1ecqn4YwB}\n }"
        ),
    },
    arima={
        "Abstract": (
            "The AutoARIMA model is a classic autoregressive model that automatically explores ARIMA"
            "models with a step-wise algorithm using Akaike Information Criterion. It applies to "
            "seasonal and non-seasonal data and has a proven record in the M3 forecasting competition. "
            "An efficient open-source version of the model was only available in R but is now also "
            "available in Python. [StatsForecast: Lightning fast forecasting with statistical and "
            "econometric models](https://github.com/Nixtla/statsforecast)."
        ),
        "Intended use": (
            "The AutoARIMA is an univariate forecasting model, intended to produce automatic "
            "predictions for large numbers of time series."
        ),
        "Secondary use": (
            "It is a classical model and is an almost obligated forecasting baseline."
        ),
        "Limitations": (
            "ARIMA model uses a recurrent prediction strategy. It concatenates errors on long "
            "horizon forecasting settings. It is a fairly simple model that does not model "
            "non-linear relationships."
        ),
        "Training data": (
            "The AutoARIMA is a univariate model that uses only autorregresive data from "
            "the target variable."
        ),
        "Citation Info": (
            "@article{hyndman2008auto_arima,"
            "title={Automatic Time Series Forecasting: The forecast Package for R},\n"
            "author={Hyndman, Rob J. and Khandakar, Yeasmin},\n"
            "volume={27},\n"
            "url={https://www.jstatsoft.org/index.php/jss/article/view/v027i03},\n"
            "doi={10.18637/jss.v027.i03},\n"
            "number={3},\n"
            "journal={Journal of Statistical Software},\n"
            "year={2008},\n"
            "pages={1–22}\n"
            "}"
        ),
    },
    exp_smoothing={
        "Abstract": (
            "Exponential smoothing is a classic technique using exponential window functions, "
            "and one of the most successful forecasting methods. It has a long history, the "
            "name was coined by Charles C. Holt. [Holt, Charles C. (1957). Forecasting Trends "
            'and Seasonal by Exponentially Weighted Averages". Office of Naval Research '
            "Memorandum.](https://www.sciencedirect.com/science/article/abs/pii/S0169207003001134)."
        ),
        "Intended use": (
            "Simple variants of exponential smoothing can serve as an efficient baseline method."
        ),
        "Secondary use": (
            "The exponential smoothing method can also act as a low-pass filter removing "
            "high-frequency noise. "
        ),
        "Limitations": (
            "The method can face limitations if the series show strong discontinuities, or if "
            "the high-frequency components are an important part of the predicted signal."
        ),
        "Training data": (
            "Just like the ARIMA method, exponential smoothing uses only autorregresive data "
            " from the target variable."
        ),
        "Citation Info": (
            "@article{holt1957exponential_smoothing, \n"
            "title = {Forecasting seasonals and trends by exponentially weighted moving averages},\n"
            "author = {Charles C. Holt},\n"
            "journal = {International Journal of Forecasting},\n"
            "volume = {20},\n"
            "number = {1},\n"
            "pages = {5-10}\n,"
            "year = {2004(1957)},\n"
            "issn = {0169-2070},\n"
            "doi = {https://doi.org/10.1016/j.ijforecast.2003.09.015},\n"
            "url = {https://www.sciencedirect.com/science/article/pii/S0169207003001134},\n"
            "}"
        ),
    },
    prophet={
        "Abstract": (
            "Prophet is a widely used forecasting method. Prophet is a nonlinear regression model."
        ),
        "Intended use": ("Prophet can serve as a baseline method."),
        "Secondary use": (
            "The Prophet model is also useful for time series decomposition."
        ),
        "Limitations": (
            "The method can face limitations if the series show strong discontinuities, or if "
            "the high-frequency components are an important part of the predicted signal."
        ),
        "Training data": (
            "Just like the ARIMA method and exponential smoothing, Prophet uses only autorregresive data "
            " from the target variable."
        ),
        "Citation Info": (
            "@article{doi:10.1080/00031305.2017.1380080,\n"
            "author = {Sean J. Taylor and Benjamin Letham},\n"
            "title = {Forecasting at Scale},\n"
            "journal = {The American Statistician},\n"
            "volume = {72},\n"
            "number = {1},\n"
            "pages = {37-45},\n"
            "year  = {2018},\n"
            "publisher = {Taylor & Francis},\n"
            "doi = {10.1080/00031305.2017.1380080},\n"
            "URL = {https://doi.org/10.1080/00031305.2017.1380080},\n"
            "eprint = {https://doi.org/10.1080/00031305.2017.1380080},\n"
            "}"
        ),
    },
)
