from fingerprint import Fingerprint
import MySQLdb as mdb


def get_consistent_ids(cur):  #过滤掉一些奇怪的变化大的不能用于实验的id,这里面有一个比例，可以考虑调整一下.最后返回一些可用于实验的id
    """
        Returns a list of user ids having only consistent fingerprints
    """

    batch_size = 5000
    # batch_size = 2
    attributes = Fingerprint.INFO_ATTRIBUTES + Fingerprint.HTTP_ATTRIBUTES + \
                     Fingerprint.JAVASCRIPT_ATTRIBUTES + Fingerprint.FLASH_ATTRIBUTES
    counter_to_os = dict()
    counter_to_browser = dict()
    id_to_oses = dict()
    id_to_browsers = dict()
    id_to_nb_inconsistencies = dict()
    id_to_nb_fps = dict()

    cur.execute('SELECT max(counter) as nb_fps from extensionDataScheme') #在表中找到counter的最大值并以nb_fps作为别名返回
    nb_fps = cur.fetchone()["nb_fps"] +1  #15001
    # nb_fps = 5

    for i in range(0, nb_fps, batch_size):  #0<=i<15001,步长为5000
        print(i)  ##0，5000，10000，15000
        sql = "SELECT * FROM extensionDataScheme where counter < %s and counter > %s"
        cur.execute(sql, (i + batch_size, i))  #0<i<5000,5000<i<10000,10000<i<15000
        fps = cur.fetchall()
        for fp_dict in fps:
            # print(fp_dict)
            try:
                fp = Fingerprint(attributes, fp_dict)
                # print(fp.getOs())
                counter_to_os[fp.getCounter()] = fp.getOs()
                # print(counter_to_os) {1:'win7',2:'win8'}
                counter_to_browser[fp.getCounter()] = fp.getBrowser()
                # print(counter_to_browser)  {1: 'Firefox', 2: 'Firefox'}
                counter = fp.getCounter()

                if fp.getId() in id_to_oses:
                    id_to_oses[fp.getId()].add(fp.getOs())
                else:
                    id_to_oses[fp.getId()] = set()  #set类型不允许重复
                    id_to_oses[fp.getId()].add(fp.getOs())
                # print(id_to_oses) {'id1':{'os1','os2'},'id2':{'os2'}}

                if fp.getId() in id_to_browsers:
                    id_to_browsers[fp.getId()].add(fp.getBrowser())
                else:
                    id_to_browsers[fp.getId()] = set()
                    id_to_browsers[fp.getId()].add(fp.getBrowser())

                if len(id_to_browsers[fp.getId()]) > 1 or len(id_to_oses[fp.getId()]) > 1:
                    id_to_nb_inconsistencies[fp.getId()] = 100000000

                if counter_to_os[counter] == "Android" or counter_to_os[counter] == "iOS" or \
                counter_to_os[counter] == "Windows Phone" or counter_to_os[counter] == "Firefox OS" or \
                counter_to_os[counter] == "Windows 95":
                    id_to_nb_inconsistencies[fp.getId()] = 10000000000

                if counter_to_browser[counter] == "Safari" or counter_to_browser[counter] == "IE" or \
                counter_to_browser[counter] == "Edge" or counter_to_browser[counter] == "Googlebot":
                    id_to_nb_inconsistencies[fp.getId()] = 10000000

                if fp.hasPlatformInconsistency():
                    if fp.getId() in id_to_nb_inconsistencies:
                        id_to_nb_inconsistencies[fp.getId()] += 5
                    else:
                        id_to_nb_inconsistencies[fp.getId()] = 5

                # id_to_nb_fps里面包含了全部的id及其各有多少条指纹
                if fp.getId() in id_to_nb_fps:
                    id_to_nb_fps[fp.getId()] += 1
                else:
                    id_to_nb_fps[fp.getId()] = 1

                # Seems weird but made on purpose !
                if fp.getId() not in id_to_nb_inconsistencies:
                    id_to_nb_inconsistencies[fp.getId()] = 0

            except:
                id_to_nb_inconsistencies[fp_dict["id"]] = 1000000

    # 这里是按照比例进行淘汰的，所以可以考虑修改上面的大数，因为共享的指纹一共才15000条
    user_id_consistent = [x for x in id_to_nb_fps if
                          float(id_to_nb_inconsistencies[x])/float(id_to_nb_fps[x]) < 0.02]
    # we remove user that poison their canvas
    # we select users that changed canvas too frequently
    cur.execute("SELECT id, count(distinct canvasJSHashed) as count, count(canvasJSHashed) as \
                nb_fps FROM extensionDataScheme group by id having count(distinct canvasJSHashed)/count(canvasJSHashed) > 0.35 \
                and count(canvasJSHashed) > 5 order by id")
    rows = cur.fetchall()
    poisoner_ids = [row["id"] for row in rows]
    #去掉属于poisoner_ids的id，剩下的都可以用于实验
    user_id_consistent = [user_id for user_id in user_id_consistent if user_id not in poisoner_ids]

    return user_id_consistent


# 取出符合条件的id和其指纹，指纹数至少6条，按时间排序，返回一个指纹集
def get_fingerprints_experiments(cur, min_nb_fingerprints, attributes, id_file="./data/consistent_extension_ids.csv"):
    """
        Returns a list of the fingerprints to use for the experiment
        We get only fingerprints whose associated user has at least
        min_nb_fingerprints and who have no inconsistency
    """
    with open(id_file, "r") as f:
        # we jump header
        f.readline()
        # print ("f.readline(): %s " % f.readline())
        ids_query = []

        for line in f.readlines():
            # print ("line: %s" % line)
            ids_query.append("'" + line.replace("\n", "") + "'")
            # print ("1.ids_query: %s " % ids_query)

        ids_query = ",".join(ids_query)
        # print ("2.ids_query: %s " % ids_query)
        # 取出预处理后的至少具有6条指纹的浏览器id的各指纹特征值，按照counter即时间排序
        cur.execute("SELECT *, NULL as canvasJS FROM extensionDataScheme WHERE \
                    id in ("+ids_query+") and \
                    id in (SELECT id FROM extensionDataScheme GROUP BY \
                    id having count(*) > "+str(min_nb_fingerprints)+")\
                    ORDER by counter ASC")
        fps = cur.fetchall()
        # print ("fps: %s" % fps)
        fp_set = []
        for fp in fps:
            # print ("fp: %s" % fp)
            try:
                fp_set.append(Fingerprint(attributes, fp))
            except Exception as e:
                print(e)

        return fp_set
