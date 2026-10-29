const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = name => fs.readFileSync(path.join(__dirname, '../public', name), 'utf8');
function storage() { const values=new Map();return { getItem:key=>values.get(key)||null, setItem:(key,value)=>values.set(key,value), removeItem:key=>values.delete(key) }; }
function factory() { const context={};vm.createContext(context);vm.runInContext(source('connection-store.js'),context);return context.DaveflixConnectionStore; }
test('trusted connection survives a new browser session; disconnect forgets it',()=>{
 const local=storage(), create=factory();let store=create(local,storage());
 assert.equal(store.save('https://pc.example','private-key',true),true);
 store=create(local,storage());assert.equal(store.read().remembered,true);assert.equal(store.read().key,'private-key');
 store.clear();assert.equal(create(local,storage()).read(),null);
});
test('untrusted connection expires with the session and remembers legacy tabs',()=>{
 const local=storage(),session=storage(),create=factory(),store=create(local,session);
 store.save('https://pc.example','key',false);assert.equal(store.read().remembered,false);
 assert.equal(create(local,storage()).read(),null);
 store.clear();session.setItem('daveflix-server','https://old.example');session.setItem('daveflix-key','old-key');
 assert.equal(store.read().url,'https://old.example');store.clear();assert.equal(store.read(),null);
});
test('opting out removes an earlier persistent connection; blocked storage reports failure',()=>{
 const local=storage(),session=storage(),create=factory(),store=create(local,session);
 store.save('https://pc.example','key',true);store.save('https://pc.example','key',false);
 assert.equal(create(local,storage()).read(),null);
 const blocked={getItem(){throw Error()},setItem(){throw Error()},removeItem(){throw Error()}};
 assert.equal(create(blocked,blocked).read(),null);assert.equal(create(blocked,blocked).save('url','key',true),false);
});
function app(fetch){
 const local=storage(), session=storage(), nodes=new Map(), timers=new Map();let timerId=0;
 local.setItem('daveflix-connection',JSON.stringify({url:'https://pc.example',key:'key'}));
 const node=id=>{if(!nodes.has(id))nodes.set(id,{value:'',innerHTML:'',textContent:'',checked:false,open:false,addEventListener(){},pause(){},load(){},removeAttribute(){},showModal(){this.open=true},close(){this.open=false}});return nodes.get(id)};
 const context={location:{hostname:'daveflix.example',origin:'https://daveflix.example'},localStorage:local,sessionStorage:session,document:{hidden:false,querySelector:node,querySelectorAll:()=>[],addEventListener(){}},window:{addEventListener(){}},fetch,AbortSignal,URL,console,setTimeout:fn=>{timers.set(++timerId,fn);return timerId},clearTimeout:id=>timers.delete(id)};
 vm.createContext(context);vm.runInContext(source('connection-store.js'),context);vm.runInContext(source('app.js'),context);
 return {nodes,timers,context};
}
const settle=()=>new Promise(resolve=>setImmediate(resolve));
test('saved connection retries an offline PC and restores its library automatically',async()=>{
 let available=false,calls=0;const a=app(async()=>{calls++;if(!available)throw Error('offline');return {ok:true,json:async()=>({items:[{id:1,title:'Example',series:'',position:0,duration:0,saved:0}],folder:'D:\\Videos'})}});
 await settle();assert.equal(calls,1);assert.equal(a.timers.size,1);assert.match(a.nodes.get('#collection').innerHTML,/Waiting for your PC/);
 available=true;const retry=[...a.timers.values()][0];a.timers.clear();await retry();await settle();
 assert.equal(calls,2);assert.equal(a.timers.size,0);assert.match(a.nodes.get('#collection').innerHTML,/Example/);
});
test('invalid pairing key stops retries and keeps settings accessible',async()=>{
 const a=app(async()=>({ok:false,status:401,json:async()=>({error:'Pairing key missing or incorrect.'})}));await settle();
 assert.equal(a.timers.size,0);assert.match(a.nodes.get('#collection').innerHTML,/Pairing key missing/);
});
