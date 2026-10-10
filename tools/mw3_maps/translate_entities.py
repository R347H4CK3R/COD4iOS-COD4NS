#!/usr/bin/env python3
"""Strict IW5 PC numeric entity-key translation; no inferred token definitions.

The pinned upstream dictionary stays external. Values and whitespace retain
their exact source bytes. Any unknown key, including unresolved 1629, prevents
output. Translated text alone is not playable IW3 map conversion.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path

COMMIT='997c7f10264114114ddf83f85c32ae6e22f6bee9'
DICTIONARY='src/gsc/engine/iw5_pc_token.cpp'
DICTIONARY_SHA256='a74df5998a8475cdc109da3a9f58a66148e818149d6a9574d2d5c7aef5dcf5ae'
MAX_BYTES=4<<20
class TranslationError(RuntimeError):pass
class UnsupportedTokens(TranslationError):
    def __init__(self,tokens):
        self.tokens=sorted(set(tokens))
        super().__init__('Unsupported IW5 PC entity-key tokens: '+', '.join(map(str,self.tokens))+
                         '; no translated output was generated (1629 is unresolved in the verified dictionary)')

def load_dictionary(source):
    source=Path(source)
    revision=subprocess.run(['git','-C',str(source),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
    if revision!=COMMIT:raise TranslationError('gsc-tool source must be checked out at '+COMMIT)
    data=(source/DICTIONARY).read_bytes().replace(b'\r\n',b'\n')
    if hashlib.sha256(data).hexdigest()!=DICTIONARY_SHA256:raise TranslationError('Pinned PC token dictionary content differs')
    pattern=re.compile(rb'^\s*\{\s*(0x[0-9A-Fa-f]+),\s*("(?:[^"\\]|\\.)*")\s*\},?\s*$',re.M)
    result={}
    for match in pattern.finditer(data):
        token=int(match[1],16);name=json.loads(match[2])
        if token in result:raise TranslationError('Duplicate token in pinned dictionary')
        result[token]=name
    # token_count reserves 31168 slots, but this source has 31167 explicit rows;
    # the commented unresolved 0x065D entry must never become a mapping.
    if len(result)!=31167 or result.get(1668)!='classname' or 1629 in result:
        raise TranslationError('Pinned dictionary structure or sentinel tokens differ')
    return result

def translate(data,dictionary):
    if len(data)>MAX_BYTES or b'\0' in data:raise TranslationError('Entity input exceeds budget or contains NUL')
    whitespace=b' \t\r\n';size=len(data);position=0;replacements=[];unknown=[];entities=0;pairs=0
    def skip():
        nonlocal position
        while position<size and data[position] in whitespace:position+=1
    while True:
        skip()
        if position==size:break
        if data[position]!=123:raise TranslationError('Expected entity opening brace')
        position+=1;entities+=1
        if entities>65535:raise TranslationError('Entity count exceeds budget')
        while True:
            skip()
            if position==size:raise TranslationError('Unclosed entity')
            if data[position]==125:position+=1;break
            start=position
            while position<size and 48<=data[position]<=57:position+=1
            if start==position or position-start>10:raise TranslationError('Expected bounded decimal IW5 key token')
            token=int(data[start:position])
            if token>0xffffffff or position==size or data[position] not in whitespace:
                raise TranslationError('Invalid entity key token boundary')
            name=dictionary.get(token)
            if token==1629 or not name:unknown.append(token)
            else:
                if not all(32<=ord(c)<127 and c not in '"\\' for c in name):
                    raise TranslationError('Unsafe entity key name in dictionary')
                replacements.append((start,position,b'"'+name.encode('ascii')+b'"'))
            skip()
            if position==size or data[position]!=34:raise TranslationError('Expected quoted entity value')
            position+=1
            while position<size:
                byte=data[position];position+=1
                if byte==34:break
                if byte==92:
                    if position==size:raise TranslationError('Truncated quoted escape')
                    position+=1
            else:raise TranslationError('Unterminated entity value')
            if position<size and data[position] not in whitespace+b'}':raise TranslationError('Invalid quoted-value boundary')
            pairs+=1
            if pairs>1_000_000:raise TranslationError('Entity pair count exceeds budget')
    if not entities:raise TranslationError('No entities')
    if unknown:raise UnsupportedTokens(unknown)
    output=[];previous=0
    for start,end,replacement in replacements:
        output.extend((data[previous:start],replacement));previous=end
    output.append(data[previous:])
    return b''.join(output)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gsc-tool-source',type=Path,required=True)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():p.error('Output exists; choose a fresh path')
    if args.output.resolve()==args.input.resolve():p.error('Preserve original entity input')
    try:
        if args.input.stat().st_size>MAX_BYTES:raise TranslationError('Entity input exceeds budget')
        original=args.input.read_bytes();converted=translate(original,load_dictionary(args.gsc_tool_source))
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('xb') as stream:stream.write(converted)
        print('Translated entity keys with pinned IW5 PC dictionary; values/layout preserved. Not a playable map.')
    except (TranslationError,OSError,subprocess.SubprocessError) as error:p.exit(1,str(error)+'\n')
if __name__=='__main__':main()
