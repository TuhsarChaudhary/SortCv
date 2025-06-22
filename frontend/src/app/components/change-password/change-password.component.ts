import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-change-password',
  templateUrl: './change-password.component.html',
  styleUrls: ['./change-password.component.css']
})
export class ChangePasswordComponent implements OnInit {
  passwordForm: FormGroup;
  loading = false;
  submitted = false;
  error = '';
  success = '';

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {
    this.passwordForm = this.fb.group({
      oldPassword: ['', Validators.required],
      newPassword: ['', [Validators.required, Validators.pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/)]],
      confirmPassword: ['', Validators.required]
    }, {
      validators: this.mustMatch('newPassword', 'confirmPassword')
    });
  }

  ngOnInit(): void {}

  get f() { return this.passwordForm.controls; }

  mustMatch(controlName: string, matchingControlName: string) {
    return (formGroup: FormGroup) => {
      const control = formGroup.controls[controlName];
      const matchingControl = formGroup.controls[matchingControlName];

      if (matchingControl.errors && !matchingControl.errors['mustMatch']) {
        return;
      }

      if (control.value !== matchingControl.value) {
        matchingControl.setErrors({ mustMatch: true });
      } else {
        matchingControl.setErrors(null);
      }
    };
  }

  onSubmit() {
    this.submitted = true;
    if (this.passwordForm.invalid) {
      return;
    }
    this.loading = true;
    this.authService.changePassword(this.f['oldPassword'].value, this.f['newPassword'].value)
      .subscribe({
        next: () => {
          this.success = 'Password changed successfully';
          this.loading = false;
          this.router.navigate(['/dashboard']);
        },
        error: err => {
          this.error = err.message || 'Failed to change password';
          this.loading = false;
        }
      });
  }
}
