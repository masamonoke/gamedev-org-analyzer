cd central
./gradlew clean
./gradlew build
./gradlew bootRun &
CENTRAL_PID=$!
echo "central pid=$CENTRAL_PID"
cd ..
cd filter/stock_predict
python main.py &
STOCK_PREDICT_PID=$!
echo "stock_predict pid=$STOCK_PREDICT_PID"
