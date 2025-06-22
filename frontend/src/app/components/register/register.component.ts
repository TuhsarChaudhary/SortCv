import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css']
})
export class RegisterComponent implements OnInit {
  registerForm: FormGroup;
  loading = false;
  submitted = false;
  error = '';

  constructor(
    private formBuilder: FormBuilder,
    private router: Router,
    private authService: AuthService
  ) { 
    this.registerForm = this.formBuilder.group({
      fname: ['', Validators.required],
      lname: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      phone: ['', [Validators.required, Validators.pattern(/^\+?[1-9]\d{1,14}$/)]],
      dateofbirth: ['', Validators.required],
      gender: ['', [Validators.required, Validators.pattern(/^(male|female|other|prefer not to say)$/i)]],
      country: ['', Validators.required],
      nationality: ['', Validators.required],
      password: ['', [Validators.required, Validators.pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/)]],
      confirmPassword: ['', Validators.required]
    }, {
      validator: this.mustMatch('password', 'confirmPassword')
    });
    
    // Redirect if already logged in
    if (this.authService.isLoggedIn()) {
      this.router.navigate(['/']);
    }
  }

  ngOnInit(): void {}

  // Custom validator to check if passwords match
  mustMatch(controlName: string, matchingControlName: string) {
    return function (formGroup: FormGroup) {
      const control = formGroup.controls[controlName];
      const matchingControl = formGroup.controls[matchingControlName];

      if (matchingControl.errors && !matchingControl.errors['mustMatch']) {
        // return if another validator has already found an error
        return;
      }

      // set error on matchingControl if validation fails
      if (control.value !== matchingControl.value) {
        matchingControl.setErrors({ mustMatch: true });
      } else {
        matchingControl.setErrors(null);
      }
    };
  }

  // Convenience getter for easy access to form fields
  get f() { return this.registerForm.controls; }

  onSubmit() {
    this.submitted = true;

    // Stop here if form is invalid
    if (this.registerForm.invalid) {
      return;
    }

    this.loading = true;
    
    const userData = {
      fname: this.f['fname'].value,
      lname: this.f['lname'].value,
      email: this.f['email'].value,
      phone: this.f['phone'].value,
      dateofbirth: this.f['dateofbirth'].value,
      gender: this.f['gender'].value,
      country: this.f['country'].value,
      nationality: this.f['nationality'].value,
      password: this.f['password'].value
    };

    this.authService.register(userData).subscribe({
      next: () => {
        // Registration successful, redirect to login page
        this.router.navigate(['/login'], { queryParams: { registered: true } });
      },
      error: error => {
        this.error = error.error?.detail || 'Registration failed. Please try again.';
        this.loading = false;
      }
    });
  }
}
