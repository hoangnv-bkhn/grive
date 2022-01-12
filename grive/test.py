print("%10s %8s" % (u'\u2601',u'\u1F4BB'))
print("%10s %10s" % (u'\U0001F5B3','\u1F4BB'))
print("%10s %10s" % (u'\u2714',u'\U0001F501'))
print("%10s %10s" % (u'\u27F3',u'\U0001F501'))
import os
# from prettytable import PrettyTable
# x = PrettyTable()

# x.field_names = ["City name", "Area", "Population", "Annual Rainfall"]
# x.add_row(["Adelaide", 1295, 1158259, 600.5])
# x.add_row(["Brisbane", 5905, 1857594, 1146.4])
# x.add_row(["Darwin", 112, 120900, 1714.7])
# x.add_row(["Hobart", 1357, 205556, 619.5])
# x.add_row(["Sydney", 2058, 4336374, 1214.8])
# x.add_row(["Melbourne", 1566, 3806092, 646.9])
# x.add_row(["Perth", 5386, 1554769, 869.4])

# print(x)
instance_id = os.getxattr("/home/tadanghuy/Documents/sync_grive/test/folder", 'user.id').decode()
print(instance_id)