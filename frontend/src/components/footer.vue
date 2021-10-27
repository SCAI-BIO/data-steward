<template>
  <div class="footer-fixed">
    <footer class="page-footer light-blue-bg">
      
      <div class="footer-copyright">
        <div class="container">
          Copyright &#169; 2021 Fraunhofer SCAI
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
    name: "Footer"
};
</script>

<style scoped>
.light-blue-bg{
  background-color: #5AA8EA !important; 
}
.footer-fixed {
	position: fixed;
	bottom: 0;
	width: 100%;
}


</style>