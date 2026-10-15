// BOUTIQUE — JS spécifique (extrait de boutique.html)
// Panier en version boutique (rendu inline) + favoris, filtres et recherche.
// NB : addToCart/renderCart/toggleCart existent aussi dans main.js (page
// accueil) avec un rendu par classes ; ici les implémentations inline du
// mock sont conservées à l'identique pour un rendu pixel-identique.

var cart=[];
function addToCart(name,price){
  var existing=cart.find(function(i){return i.name===name});
  if(existing){existing.qty++}else{cart.push({name:name,price:price,qty:1})}
  renderCart();
  var el=document.getElementById('cartCount');
  el.classList.remove('pop');void el.offsetWidth;el.classList.add('pop');
}
function removeFromCart(idx){cart.splice(idx,1);renderCart()}
function renderCart(){
  var count=cart.reduce(function(s,i){return s+i.qty},0);
  document.getElementById('cartCount').textContent=count;
  var itemsEl=document.getElementById('cartItems');
  var emptyEl=document.getElementById('cartEmpty');
  if(!cart.length){itemsEl.innerHTML='';emptyEl.style.display='block';document.getElementById('cartTotal').textContent='0€';return}
  emptyEl.style.display='none';
  var html='';var total=0;
  cart.forEach(function(item,idx){
    var sub=item.price*item.qty;total+=sub;
    html+='<div style="display:flex;justify-content:space-between;align-items:center;padding:12px;border-radius:12px;background:var(--bg);margin-bottom:8px"><div><h4 style="font-size:.92rem;margin-bottom:2px">'+item.name+(item.qty>1?' x'+item.qty:'')+'</h4><p style="font-size:.78rem;color:#636E72">'+item.price.toFixed(2).replace('.',',')+'€ / unité</p></div><div style="display:flex;align-items:center;gap:6px"><span style="font-weight:700;font-family:var(--fh);color:var(--rose)">'+sub.toFixed(2).replace('.',',')+'€</span><button style="background:none;border:none;color:#bbb;font-size:1.1rem" onclick="removeFromCart('+idx+')">&times;</button></div></div>';
  });
  itemsEl.innerHTML=html;
  document.getElementById('cartTotal').textContent=total.toFixed(2).replace('.',',')+'€';
}
function toggleCart(){
  var overlay=document.getElementById('cartOverlay'),drawer=document.getElementById('cartDrawer');
  if(overlay.style.opacity==='1'){overlay.style.opacity='0';overlay.style.pointerEvents='none';drawer.style.right='-440px'}
  else{overlay.style.opacity='1';overlay.style.pointerEvents='auto';drawer.style.right='0'}
}
function validateCart(){
  if(!cart.length){alert('Votre panier est vide !');return}
  alert('Commande validée ! Vous recevrez un email de confirmation.');
  cart=[];renderCart();toggleCart();
}

var likedProducts=JSON.parse(localStorage.getItem('minivers_likes')||'[]');

function toggleLike(btn){
  var name=btn.getAttribute('data-name');
  var index=likedProducts.indexOf(name);
  if(index===-1){likedProducts.push(name);btn.classList.add('liked')}
  else{likedProducts.splice(index,1);btn.classList.remove('liked')}
  localStorage.setItem('minivers_likes',JSON.stringify(likedProducts));
  updateFavoritesCount();
  var activeChip=document.querySelector('.filter-chip.active');
  if(activeChip&&activeChip.dataset.cat==='favorites'){filterProducts('favorites')}
}

function updateFavoritesCount(){
  var el=document.querySelector('[data-cat="favorites"] .chip-count');
  if(el){el.textContent='('+likedProducts.length+')'}
}

function filterProducts(cat){
  var products=document.querySelectorAll('.product');
  for(var i=0;i<products.length;i++){
    var p=products[i];var name=p.dataset.name;
    if(cat==='all'){p.style.display='flex'}
    else if(cat==='favorites'){p.style.display=likedProducts.includes(name)?'flex':'none'}
    else{p.style.display=p.dataset.cat===cat?'flex':'none'}
  }
}

var searchInput=document.getElementById('searchInput');
if(searchInput){
  searchInput.addEventListener('input',function(e){
    var term=e.target.value.toLowerCase().trim();
    var products=document.querySelectorAll('.product');
    var activeChip=document.querySelector('.filter-chip.active');
    var cat=activeChip?activeChip.dataset.cat:'all';
    for(var i=0;i<products.length;i++){
      var p=products[i];
      var name=p.dataset.name.toLowerCase();
      var desc=p.querySelector('.product-desc')?p.querySelector('.product-desc').textContent.toLowerCase():'';
      var searchText=name+' '+desc;
      var matchesSearch=!term||searchText.includes(term);
      var matchesCat=true;
      if(cat==='all'){matchesCat=true}
      else if(cat==='favorites'){matchesCat=likedProducts.includes(p.dataset.name)}
      else{matchesCat=p.dataset.cat===cat}
      p.style.display=(matchesSearch&&matchesCat)?'flex':'none';
    }
  });
}

var chips=document.querySelectorAll('.filter-chip');
for(var i=0;i<chips.length;i++){
  (function(chip){
    chip.addEventListener('click',function(){
      for(var j=0;j<chips.length;j++){chips[j].classList.remove('active')}
      chip.classList.add('active');
      filterProducts(chip.dataset.cat);
    });
  })(chips[i]);
}

var grid=document.getElementById('shopGrid');
if(grid){
  grid.addEventListener('click',function(e){
    var likeBtn=e.target.closest('.btn-like');
    if(likeBtn){
      toggleLike(likeBtn);
      return;
    }
    var cartBtn=e.target.closest('[data-action="cart"]');
    if(cartBtn){
      var name=cartBtn.getAttribute('data-name');
      var price=parseFloat(cartBtn.getAttribute('data-price'));
      addToCart(name,price);
    }
  });
}

document.addEventListener('DOMContentLoaded',function(){
  for(var i=0;i<likedProducts.length;i++){
    var btn=document.querySelector('button[data-name="'+likedProducts[i]+'"]');
    if(btn){btn.classList.add('liked')}
  }
  updateFavoritesCount();
});
