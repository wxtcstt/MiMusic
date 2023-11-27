import unicodedata
import pypinyin


def get_duration(file_path):
    return 10
    
def is_chinese(character):
    """判断一个字符是否是中文"""
    return 'CJK' in unicodedata.name(character)

def ChineseToPinyin(hanzi):
    pinyin=pypinyin.pinyin(hanzi, style=pypinyin.NORMAL)
    return pinyin[0][0]

def musicIndexName(musicrawname):
    '''
    音乐名字要求[作者]-音乐名，其中作者可选，例如 七里香 或者周杰伦-七里香
    音乐名字对应的索引名字
    '''
    indexname=""
    for  chr in musicrawname:
        if is_chinese(chr):
            indexname+=ChineseToPinyin(chr)
        else:
            indexname+=chr
    musicrawname=musicrawname[0:musicrawname.find(".") if musicrawname.find(".")>=0 else -1]
    wakename=[]
    author=""
    puremusicname=musicrawname
    if "-" in musicrawname:
        author=musicrawname.split("-")[0].strip()
        puremusicname=musicrawname.split("-")[1].strip()
    wakename.append(puremusicname)
    if author:
       wakename.append(author+"的"+puremusicname)
    if author=="":
        author="未知"
    return indexname,wakename,author,puremusicname

    