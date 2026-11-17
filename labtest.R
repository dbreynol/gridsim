set.seed(0815)

N <- 500

ab_test_data <- data.frame( order_id = 1:N,

revenue = rlnorm(N, meanlog = 3.8, sdlog = 0.3),

processing_days = rnorm(N, mean = 4.3, sd = 1.2),

client_is_enterprise = rbinom(N, size = 1, prob = 0.18) )

xbar = mean(ab_test_data$processing_days)

pnorm(xbar, 4.5, 1.2/sqrt(500))

xbar_reb = mean(ab_test_data$revenue)
se_rev = 15/sqrt(500)
(xbar_reb - 45)/se_rev


pbar = mean(ab_test_data$client_is_enterprise)
sqrt(.15 * .85 / 500)

1-pnorm(pbar, .15, sqrt(.15 * .85 / 500))
