library(dplyr)
library(readr)
library(lubridate)
library(plm)
library(stringr)
library(lmtest)

run_and_print <- function(label, model) {
    cat("\n===", label, "===\n")
    print(summary(model))
}

build_model_data <- function(data, avg_first10_table = NULL) {
    data_use <- data
    if (!is.null(avg_first10_table)) {
        data_use <- data_use %>%
            select(-avg_first10_score) %>%
            inner_join(avg_first10_table, by = c("speaker_name_clean" = "name_clean"))
    }

    data_use %>%
        filter(
            !is.na(speaker_points),
            !is.na(avg_first10_score),
            !is.na(lag_avg_teammate_score),
            !is.na(tournament_round),
            !is.na(motion_balance),
            !is.na(motion_balance_x_aff)
        ) %>%
        mutate(speaker_id = as.integer(as.factor(speaker_name_clean))) %>%
        arrange(speaker_id, debate_date)
}

make_mundlak_data <- function(model_df, min_obs = 10) {
    model_df %>%
        arrange(speaker_id, debate_date, debate_id) %>%
        group_by(speaker_id) %>%
        mutate(time_index = row_number()) %>%
        ungroup() %>%
        group_by(speaker_id) %>%
        filter(n() >= min_obs) %>%
        mutate(
            mean_lag_avg_teammate_score = mean(lag_avg_teammate_score, na.rm = TRUE),
            mean_tournament_round = mean(tournament_round, na.rm = TRUE),
            lag_avg_teammate_score_c = lag_avg_teammate_score - mean_lag_avg_teammate_score,
            tournament_round_c = tournament_round - mean_tournament_round
        ) %>%
        ungroup() %>%
        mutate(
            avg_first10_score_z = as.numeric(scale(avg_first10_score)),
            lag_avg_teammate_score_c_z = as.numeric(scale(lag_avg_teammate_score_c)),
            tournament_round_c_z = as.numeric(scale(tournament_round_c)),
            mean_lag_avg_teammate_score_z = as.numeric(scale(mean_lag_avg_teammate_score)),
            mean_tournament_round_z = as.numeric(scale(mean_tournament_round))
        )
}

base_dir <- "c:/Users/QX163MQ/Downloads/non-work/school/data processing in python/project/speaker_stats"
scores_path <- file.path(base_dir, "scraping/debate_natural_ability_scraping/speaker_scores.csv")
final_path  <- file.path(base_dir, "data/processed/final_joined_data.csv")

clean_name <- function(x) {
    x %>%
        str_replace_all('"[^"]*"', "") %>%  # remove nicknames in quotes
        str_squish()
}

# Load and prep speaker_scores
scores <- read_csv(scores_path, show_col_types = FALSE) %>%
    mutate(
        debate_date = ymd(debate_date),
        speaker_score_num = suppressWarnings(as.numeric(speaker_score)),
        name_clean = clean_name(name)
    ) %>%
    filter(!is.na(debate_date), !is.na(speaker_score_num), !is.na(name_clean)) %>%
    arrange(name_clean, debate_date)

avg_first10 <- scores %>%
    group_by(name_clean) %>%
    slice_head(n = 10) %>%
    summarise(avg_first10_score = mean(speaker_score_num), .groups = "drop")

avg_first10_strict <- scores %>%
    group_by(name_clean) %>%
    filter(n() >= 10) %>%
    slice_head(n = 10) %>%
    summarise(avg_first10_score = mean(speaker_score_num), .groups = "drop")

# Load final data
df <- read_csv(final_path, show_col_types = FALSE) %>%
    mutate(
        speaker_name_clean = str_squish(speaker_name),
        debate_date = ymd_hms(debate_date),
        speaker_first_debate_date = ymd(speaker_first_debate_date)
    ) %>%
    inner_join(avg_first10, by = c("speaker_name_clean" = "name_clean"))

# Feature engineering (same as notebook)
motion_balance <- df %>%
    filter(side == "aff") %>%
    group_by(debate_id, motion) %>%
    summarise(ballots_gained = mean(ballots_gained, na.rm = TRUE), .groups = "drop") %>%
    group_by(motion) %>%
    summarise(motion_balance = mean(ballots_gained, na.rm = TRUE), .groups = "drop")

df <- df %>%
    left_join(motion_balance, by = "motion") %>%
    mutate(
        years_since_first_debate = year(debate_date) - year(speaker_first_debate_date),
        tournament_round = ave(debate_date, tournament_id, FUN = function(x) rank(x, ties.method = "first")),
        is_aff = if_else(side == "aff", 1, 0),
        motion_balance_x_aff = motion_balance * is_aff
    )

get_teammate_avg <- function(x) {
    sapply(seq_along(x), function(i) mean(x[-i], na.rm = TRUE))
}

df <- df %>%
    group_by(debate_id, side) %>%
    mutate(avg_teammate_score = get_teammate_avg(speaker_points)) %>%
    ungroup() %>%
    arrange(speaker_name_clean, debate_date, debate_id) %>%
    group_by(speaker_name_clean) %>%
    mutate(lag_avg_teammate_score = lag(cummean(avg_teammate_score))) %>%
    ungroup()

# Model data
df_model <- build_model_data(df)
df_model_strict <- build_model_data(df, avg_first10_table = avg_first10_strict)

# Pooled OLS
pool_formula <- speaker_points ~ avg_first10_score + is_male + lag_avg_teammate_score +
    tournament_round

run_panel_models <- function(data, formula, index = c("speaker_id", "debate_date")) {
    pool <- plm(formula, data = data, model = "pooling", index = index)
    re <- plm(formula, data = data, model = "random", index = index)
    fe <- plm(formula, data = data, model = "within", index = index)

    list(
        pool = pool,
        re = re,
        fe = fe,
        lm_test = plmtest(pool, type = "bp"),
        hausman_test = phtest(fe, re)
    )
}

panel_models <- run_panel_models(df_model, pool_formula)
panel_models_strict <- run_panel_models(df_model_strict, pool_formula)

run_and_print("Pooled OLS", panel_models$pool)
run_and_print("Random Effects", panel_models$re)
run_and_print("Fixed Effects", panel_models$fe)
print(panel_models$lm_test)
print(panel_models$hausman_test)

run_and_print("Pooled OLS (Strict)", panel_models_strict$pool)
run_and_print("Random Effects (Strict)", panel_models_strict$re)
run_and_print("Fixed Effects (Strict)", panel_models_strict$fe)
print(panel_models_strict$lm_test)
print(panel_models_strict$hausman_test)


df_mundlak <- make_mundlak_data(df_model, min_obs = 10)
df_mundlak_strict <- make_mundlak_data(df_model_strict, min_obs = 10)

colinearity_test <- lm(speaker_points ~ lag_avg_teammate_score_c + mean_lag_avg_teammate_score + tournament_round_c + mean_tournament_round, data = df_mundlak)
summary(colinearity_test)

mundlak_formula <- speaker_points ~ avg_first10_score_z + is_male +
    lag_avg_teammate_score_c_z + tournament_round_c_z +
    mean_lag_avg_teammate_score_z + mean_tournament_round_z

mundlak_formulas <- list(
    full = mundlak_formula,
    no_mean_round = speaker_points ~ avg_first10_score_z + is_male +
        lag_avg_teammate_score_c_z + tournament_round_c_z +
        mean_lag_avg_teammate_score_z,
    no_mean_lag = speaker_points ~ avg_first10_score_z + is_male +
        lag_avg_teammate_score_c_z + tournament_round_c_z +
        mean_tournament_round_z
)

run_mundlak_models <- function(formula, data, label_prefix = "") {
    mod <- plm(
        formula,
        data = data,
        model = "random",
        index = c("speaker_id", "time_index")
    )
    run_and_print(paste0(label_prefix, "Mundlak"), mod)
    mod
}

run_mundlak_pooled <- function(formula, data, label_prefix = "") {
    mod <- plm(
        formula,
        data = data,
        model = "pooling",
        index = c("speaker_id", "time_index")
    )
    cat("\n===", label_prefix, "Mundlak pooled (clustered SEs)", "===\n")
    print(coeftest(mod, vcov = vcovHC(mod, type = "HC1", cluster = "group")))
    mod
}

mundlak_mod <- run_mundlak_models(mundlak_formulas$full, df_mundlak)
mundlak_mod_strict <- run_mundlak_models(mundlak_formulas$full, df_mundlak_strict, "Strict ")


# mundlak with dropped mean terms
mundlak_no_mean_round <- run_mundlak_models(mundlak_formulas$no_mean_round, df_mundlak, "No mean round ")
mundlak_no_mean_round_strict <- run_mundlak_models(mundlak_formulas$no_mean_round, df_mundlak_strict, "No mean round (Strict) ")

mundlak_no_mean_lag <- run_mundlak_models(mundlak_formulas$no_mean_lag, df_mundlak, "No mean lag ")
mundlak_no_mean_lag_strict <- run_mundlak_models(mundlak_formulas$no_mean_lag, df_mundlak_strict, "No mean lag (Strict) ")

mundlak_pooled <- run_mundlak_pooled(mundlak_formulas$full, df_mundlak)
mundlak_pooled_strict <- run_mundlak_pooled(mundlak_formulas$full, df_mundlak_strict, "Strict ")


# DEBUG
df_mundlak %>%
    count(speaker_id, name = "n_obs") %>%
    arrange(n_obs)

df_mundlak %>%
    group_by(speaker_id) %>%
    summarise(
        n_obs = n(),
        var_lag = var(lag_avg_teammate_score, na.rm = TRUE),
        var_round = var(tournament_round, na.rm = TRUE)
    ) %>%
    filter(n_obs < 3 | is.na(var_lag) | var_lag == 0 | is.na(var_round) | var_round == 0)

df_mundlak %>%
    group_by(speaker_id) %>%
    summarise(
        const_lag = n_distinct(lag_avg_teammate_score) == 1,
        const_round = n_distinct(tournament_round) == 1
    ) %>%
    filter(const_lag | const_round)


gmm_formula <- speaker_points ~ lag(speaker_points, 1) + avg_first10_score_z + is_male +
    lag_avg_teammate_score_c_z + tournament_round_c_z +
    mean_lag_avg_teammate_score_z + mean_tournament_round_z |
    lag(speaker_points, 2:5)

gmm_mod <- pgmm(
    gmm_formula,
    data = df_mundlak,
    effect = "individual",
    model = "twosteps",
    transformation = "d",
    index = c("speaker_id", "time_index")
)

gmm_mod_strict <- pgmm(
    gmm_formula,
    data = df_mundlak_strict,
    effect = "individual",
    model = "twosteps",
    transformation = "d",
    index = c("speaker_id", "time_index")
)

run_and_print("GMM", gmm_mod)
run_and_print("GMM Strict", gmm_mod_strict)



#Check rank deficienc:
m <- model.matrix(mundlak_formula, df_mundlak)
qr(m)$rank; ncol(m)

kappa(model.matrix(mundlak_formula, df_mundlak))

#Find exact linear dependencies:
alias(lm(mundlak_formula, data = df_mundlak))

#Check duplicate (speaker_id, time_index) rows:
df_mundlak %>% count(speaker_id, time_index) %>% filter(n > 1)

# duplicate rows?

ercomp(mundlak_formula, data = df_mundlak, model = "random", effect = "individual", random.method = "swar", index = c("speaker_id", "time_index"))

pdata.frame(df_mundlak, index = c("speaker_id", "time_index")) %>%
index() %>%
table() %>%
{ .[. > 1] }