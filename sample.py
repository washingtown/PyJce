from PyJce import JceInputStream,JceStruct

f = open('cover_detail_waterfall鬼吹灯', 'rb')
stream = JceInputStream(f.read())
s=JceStruct()
s.read_from(stream)
ff = open('cover_detail_waterfall鬼吹灯.txt', 'w')
ff.write(s.to_json())
f.close()
ff.close()