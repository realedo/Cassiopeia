import yfinance as yf   #yahoo finance API for candles
import pandas as pd     #formatting/datasets library
import pytz             #timezone library
from datetime import datetime, date, timedelta
import pandas_market_calendars as mcal #gets trading days, skips days where market is not open

# timezone adjust
now = datetime.now(pytz.timezone("US/Eastern"))

print("Now in US/East:", now)
today = date.today()





#data is structered as following:
# Close, High, Low, Open, Volume

balance = 1000
start_balance=balance
top_balance = balance
fee_rate = 0.0002 #percentage
max_leverage = 4
take_position_minimum = 0.002 #minimum % slip in first candle to open the position
ticker = "NVDA"  #title symbol
start_date = "2025-06-08"
end_date = "2025-07-07"
total_plays=0
wins=0
losses=0

#strategy:

#first 5 minutes the market moved up, we took a bullish position starting 
# from the second candle’s opening price. Conversely, 
# if the first 5-minute candle was negative, we took a bearish position at 
# the open of the second 5-minute candle. No positions were opened when the 
# first 5-minute candle was a doji (open = close). The stop loss was placed at 
# the low of the day (which was the low of the first 5-minute candle) for a long trade, 
# and at the high of the day (which was the high of the first 5-minute candle) for a short trade,

#stop-entry price is risk $R

#We set the profit target at 10x the $R
#if no profit then seel last candle


#size:
#take lower between :
#Accbalance * 0.01(1%) / $R
#4(4x leverage) * AccBalance / P(opeing price)




def ORB ( candles ):       #decides the strategy for the day

    if (abs(candles.iloc[0]["Open"][ticker] - candles.iloc[0]["Close"][ticker]) / candles.iloc[0]["Open"][ticker] < take_position_minimum ): #checks if theres enough slip to make the strategy work
        return 0
    else:

        if candles.iloc[0]["Open"][ticker] < candles.iloc[0]["Close"][ticker]:

            return "long"    #long
        
        else:

            return "short"    #short


def LIMIT ( candles ):  #sets stop limits

    if ORB ( candles ) == 0:

        return 0
    
    if ORB ( candles ) == "long":

        return candles.iloc[0]["Low"][ticker]
    
    if ORB ( candles ) == "short":

        return candles.iloc[0]["High"][ticker]
    

def RISK ( candles ):   #calculates risk

    if ORB ( candles ) == 0:

        return 0
    
    else :

        return abs(candles.iloc[1]["Open"][ticker] - LIMIT( candles ))
    

def SIZE ( candles ):   #define size of trade

    if ORB ( candles ) == 0:
        
        return 0
    
    else :
        if RISK(candles)==0:
            return 1
        return int(min( (balance*0.01/RISK(candles)), (max_leverage*balance/candles.iloc[0]["Open"][ticker]) ))



def percentage( balance, profit): #gets percentage after the positoin is closed - returns a string!

    return "("+str(profit/balance*100)+"%)"

#trade now

#definese nyse as the nyse calendar - using mcal api
nyse = mcal.get_calendar("NYSE")

# only valid market days
schedule = nyse.schedule(start_date=start_date, end_date=end_date)
trading_days = schedule.index.date

# Loop through each trading day
for day in trading_days:    #for each object in trading_days

    next_day = day + timedelta(days=1) #day after using nyse calendar

    bars = yf.download(ticker, start=str(day), end=str(next_day), interval="5m", progress=False, auto_adjust=False)
    position = ORB(bars)    #strategy to be used in the day
    
    if bars.empty:  #checks if its recieving data
        print(f"{day}: No data available.")
        continue

    print(f"{day}: Data loaded with {len(bars)} candles.")
    
    # --- strategy  ---
    risk = RISK(bars)
    entry = bars.iloc[1]["Open"][ticker]
    limit = LIMIT(bars)
    take_profit = 0 #defines take profit for the day
    if position =="long":
        take_profit = entry + 10*risk
    if position =="short":
        take_profit = entry - 10*risk
    limit_reached = 0   #checks if a limit has been reached (if not closes position at last candle)
    trade_start = 0
    lots = int(SIZE(bars))
    profit = 0
    close_position =0



    print("Starting balance: "+str(balance)+"$")
    print("First candle of " + ticker + " today is " + str(round(bars.iloc[0]["Open"][ticker], 2)) + " open and " + str(round(entry, 2)) + " close.\nDetected : " + str(position) + "\nOpen slip: " + str((abs(bars.iloc[0]["Open"][ticker] - bars.iloc[0]["Close"][ticker]) / bars.iloc[0]["Open"][ticker])))
    print("Risk : "+ str(risk) +"$, stop loss: "+ str(limit) +"$")



    if position == 0:
        
        print("no hedge to be found, no position will be taken today")

    else:

        trade_start = 1
        total_plays = total_plays + 1

        if position == "long":

            if lots < 0.5*bars.iloc[1]["Volume"][ticker]: #checks if order is less then half the order book

                print("Bought " + str(lots) + " of " + ticker + " at " + str(round(entry, 2)))
                #balance = balance - entry*lots 
                
            else :
                print("Hedge was found but order could not be fulfilled")
                #balance = balance - entry*lots 
        
        else:


            if lots < 0.5*bars.iloc[1]["Volume"][ticker]:

                print("Shorted " + str(lots) + " of " + ticker + "at " + str(round(entry, 2))+"$\n")
            else :
                print("Hedge was found but order could not be fulfilled")



    if trade_start == 1:

        for i in range(2, len(bars) - 1):

            
            if position == "long":

                if bars.iloc[i]["Open"][ticker]>=take_profit:

                    close_position = bars.iloc[i]["Open"][ticker]
                    profit = (close_position - entry)*lots
                    print("Sold shares at " + str(round(close_position, 2)) + "$ totaling " + str(round(profit, 2)) + "$ profit\n")
                    limit_reached = 1
                    break
                
                if bars.iloc[i]["Open"][ticker]<=limit:

                    close_position = bars.iloc[i]["Open"][ticker]
                    profit = (close_position - entry)*lots
                    print("Stop loss reached! Sold shares at " + str(round(close_position, 2))+ "$ totaling "+str(round(profit, 2))+"$ loss")
                    limit_reached = 1
                    break
            

            else :

                if bars.iloc[i]["Open"][ticker]<=take_profit:

                    close_position = bars.iloc[i]["Open"][ticker]
                    profit = (entry - close_position)*lots
                    print("Covering shares at " + str(round(close_position, 2)) + "$ totaling " + str(round(profit, 2)) + "$ profit\n")
                    limit_reached = 1
                    break
                
                if bars.iloc[i]["Open"][ticker]>=limit:

                    close_position = bars.iloc[i]["Open"][ticker]
                    profit = (entry - close_position)*lots
                    print("Stop loss reached! Covering shares at " + str(round(close_position, 2))+ "$ totaling "+str(round(profit, 2))+"$ loss")
                    limit_reached = 1
                    break





    if limit_reached == 0:
        
        if position == "long":

            close_position = bars.iloc[-1]["Open"][ticker]
            profit = (close_position - entry)*lots
            print("No take profit limit has been reached, selling at " + str(round(close_position, 2))+"$ totaling "+str(round(profit, 2))+"$\n")


        else :
    
            close_position = bars.iloc[-1]["Open"][ticker]
            profit = (entry - close_position)*lots
            print("No take profit limit has been reached, covering at " + str(round(close_position, 2))+"$ totaling "+str(round(profit, 2))+"$\n")


    fee = entry*lots*fee_rate + close_position*lots*fee_rate
    balance = balance + profit - fee
    print("Recap:\nBalance: "+ str(round(balance, 2)) +"$\nProfit: "+ str(round(profit, 2))+"$"+ percentage(balance, profit)+"\nFees: -"+str(round(fee, 2))+"$\n\n\n")
    if profit > 0 : #records if its a win or a loss
        wins+=1
    if profit < 0:
        losses+=1   
    if balance >= top_balance:  #updates all time high

        top_balance = balance
    


print("\n\n\nClosing recap:\nBalance : "+str(round(balance, 2))+"$\nProfit perc : " + percentage(balance, balance-start_balance)+"\nTop balance : "+str(round(top_balance, 2))+"%\nStarting balance : "+str(round(start_balance, 2))+"$")
print("Total trades : "+str(total_plays))
print("Wins : "+ str(wins))
print("Losses : "+str(losses))      
print("Winrate : "+str(wins/total_plays*100)+"%")





