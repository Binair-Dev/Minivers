let cart=[];
function addToCart(name,price){
  let existing=cart.find(i=>i.name===name);
  if(existing){existing.qty++}else{cart.push({name,price,qty:1})}
  renderCart();
  let el=document.getElementById('cartCount');
  el.classList.remove('pop');void el.offsetWidth;el.classList.add('pop');
}
function removeFromCart(idx){cart.splice(idx,1);renderCart()}
function renderCart(){
  let count=cart.reduce((s,i)=>s+i.qty,0);
  document.getElementById('cartCount').textContent=count;
  let itemsEl=document.getElementById('cartItems');
  let emptyEl=document.getElementById('cartEmpty');
  if(!cart.length){itemsEl.innerHTML='';emptyEl.style.display='block';document.getElementById('cartTotal').textContent='0€';return}
  emptyEl.style.display='none';
  let html='';let total=0;
  cart.forEach((item,idx)=>{
    let sub=item.price*item.qty;total+=sub;
    html+='<div class="cart-item"><div class="cart-item-info"><h4>'+item.name+(item.qty>1?' x'+item.qty:'')+'</h4><p>'+item.price+'€ / unité</p></div><div class="cart-item-right"><span class="cart-item-price">'+sub+'€</span><button class="cart-item-rm" onclick="removeFromCart('+idx+')">&times;</button></div></div>';
  });
  itemsEl.innerHTML=html;
  document.getElementById('cartTotal').textContent=total+'€';
}
function toggleCart(){
  document.getElementById('cartOverlay').classList.toggle('open');
  document.getElementById('cartDrawer').classList.toggle('open');
}
function validateCart(){
  if(!cart.length){alert('Votre panier est vide !');return}
  alert('Réservation validée ! Vous recevrez un email de confirmation.');
  cart=[];renderCart();toggleCart();
}

// Sock banner scroll hide
window.addEventListener('scroll',function(){var b=document.getElementById('sockBanner');if(b){b.classList.toggle('hidden',window.scrollY>200)}});


(function(){
  var car=document.getElementById('mainCarousel');
  if(!car)return;
  var t=car.querySelector('.carousel-track');
  var _iv=null;
  function stop(){if(_iv){clearInterval(_iv);_iv=null}}
  car.addEventListener('mousemove',function(e){
    stop();
    var r=car.getBoundingClientRect();
    var x=e.clientX-r.left;
    var w=r.width;
    var zone=w*0.18;
    if(x<zone){
      var speed=Math.round((1-(x/zone))*10)+2;
      _iv=setInterval(function(){t.scrollBy(-speed,0)},16);
    }else if(x>w-zone){
      var speed2=Math.round(((x-(w-zone))/zone)*10)+2;
      _iv=setInterval(function(){t.scrollBy(speed2,0)},16);
    }
  });
  car.addEventListener('mouseleave',stop);
  car.addEventListener('mousedown',stop);
})();
