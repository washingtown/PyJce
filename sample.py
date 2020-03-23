from pyjce import JceInputStream,JceStruct

f = open('datas', 'rb')
stream = JceInputStream(f.read())
s=JceStruct()
s.read_from(stream)
ff = open('datas.txt', 'w')
print(s.to_json())
ff.write(s.to_json())
f.close()
ff.close()
