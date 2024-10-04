# This script shows how the graphs data points were created.
myList = []
#i* random.random() > MAX_RANDOMIZER*random.random()
# to plot this graph
#y=sum[n=0, n->x]((1/(x+1)) * min(1,n/MAX_RANOMIZER))
MAX_DATA = 100
MAX_RANDOMIZER = 15
for i in range(MAX_DATA):
    sum_prob = 0
    for j in range(i+1):
        prob_j_higher = min(j/MAX_RANDOMIZER,1)
        prob_j = 1/(i+1)
        sum_prob += (prob_j * prob_j_higher)
    myList.append(sum_prob)

print(myList)
print(len(myList))