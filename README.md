# Cassiopeia
simple ORB strategy backtester

# Introduction
this is a simple python backtester that uses yfinance to predict stock prices using the folllowing paper:
Can Day Trading Really Be Profitable? By Carlo Zarattini, Andrew Aziz.
Since its using yfinance API to fetch data, like in my realedo/CandlestickFetcher, it can only go back as far as 30 days.

# Fetures
includes tracking of number of trades and their win/loss percentage, balance and profit update on each trade and a closing recap of the 30-days backtest.
It also uses the pandas market calendars library to only fetch data from actual market days.
