import os
import re


wb_data = []
all_time = []
loss_train_data = []
acc_train_data = []
loss_test_data = []
acc_test_data = []
i = 2
with open('analyse/analysis_acc.xls', 'r') as f:
    for line in f:
        # print())
        if (i%4) == 0:
            # print(float(line.strip('\n').split(' ')[5]))
            loss_train_data.append(float(line.strip('\n').split(' ')[5]))
            acc_train_data.append(float(line.strip('\n').split(' ')[8]))
            loss_test_data.append(float(line.strip('\n').split(' ')[14]))
            acc_test_data.append(float(line.strip('\n').split(' ')[17]))
        i+=1
        # print(i)
print(loss_train_data,acc_train_data,loss_test_data,acc_test_data)

with open("analyse/analysis_loss.xls", "a") as f:
    f.write("\n%s\n" % ("acc_test"))
#     # don't iterate over reals_ids since some fps don't have end date and are not present
    for i in acc_test_data:
        f.write("%s\n" % i)
